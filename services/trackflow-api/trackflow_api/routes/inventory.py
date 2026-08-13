from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from ..core.cache import (
    INVENTORY_ORDERS_KEY,
    INVENTORY_PREFIX,
    INVENTORY_PRODUCTS_KEY,
    cache_get,
    cache_invalidate_prefix,
    cache_set,
)
from ..core.database import get_sql_session
from ..core.security import get_current_user
from ..models import SKU, StockEntry, StockExit
from ..schemas.inventory import (
    InventoryMovementRead,
    SKUCreate,
    SKURead,
    StockEntryCreate,
    StockEntryRead,
    StockExitCreate,
    StockExitRead,
)
from ..schemas.users import UserPublic


router = APIRouter(prefix="/inventory")

PRODUCTS_CACHE_TTL_SECONDS = 20
ORDERS_CACHE_TTL_SECONDS = 30


def _compute_current_stock(session: Session, sku_id: int, warehouse: str) -> int:
    entry_total = session.exec(
        select(func.coalesce(func.sum(StockEntry.quantity), 0)).where(
            StockEntry.sku_id == sku_id,
            StockEntry.warehouse == warehouse,
        )
    ).one()
    exit_total = session.exec(
        select(func.coalesce(func.sum(StockExit.quantity), 0)).where(
            StockExit.sku_id == sku_id,
            StockExit.warehouse == warehouse,
        )
    ).one()
    return int(entry_total or 0) - int(exit_total or 0)


def _stock_totals_by_sku_warehouse(session: Session) -> dict[tuple[int, str], int]:
    totals: dict[tuple[int, str], int] = {}

    entry_rows = session.exec(
        select(StockEntry.sku_id, StockEntry.warehouse, func.sum(StockEntry.quantity)).group_by(
            StockEntry.sku_id,
            StockEntry.warehouse,
        )
    ).all()
    for sku_id, warehouse, total in entry_rows:
        key = (int(sku_id), str(warehouse))
        totals[key] = totals.get(key, 0) + int(total or 0)

    exit_rows = session.exec(
        select(StockExit.sku_id, StockExit.warehouse, func.sum(StockExit.quantity)).group_by(
            StockExit.sku_id,
            StockExit.warehouse,
        )
    ).all()
    for sku_id, warehouse, total in exit_rows:
        key = (int(sku_id), str(warehouse))
        totals[key] = totals.get(key, 0) - int(total or 0)

    return totals


def _invalidate_inventory_cache() -> None:
    cache_invalidate_prefix(INVENTORY_PREFIX)


def _build_product_reads(session: Session) -> list[SKURead]:
    records = session.exec(select(SKU).order_by(SKU.id)).all()
    stock_totals = _stock_totals_by_sku_warehouse(session)

    return [
        SKURead(
            id=record.id,
            name=record.name,
            sku=record.sku,
            client_name=record.client_name,
            category=record.category,
            warehouse=record.warehouse,
            current_stock=stock_totals.get((record.id, str(record.warehouse)), 0),
        )
        for record in records
    ]


def _build_order_reads(session: Session) -> list[InventoryMovementRead]:
    movement_rows: list[InventoryMovementRead] = []

    inbound_rows = session.exec(select(StockEntry, SKU).join(SKU, StockEntry.sku_id == SKU.id)).all()
    for entry, sku in inbound_rows:
        movement_rows.append(
            InventoryMovementRead(
                id=entry.id,
                movement_type="inbound",
                sku_id=entry.sku_id,
                sku=sku.sku,
                sku_name=sku.name,
                client_name=sku.client_name,
                category=sku.category,
                quantity=entry.quantity,
                warehouse=entry.warehouse,
                created_at=entry.created_at,
                user_uuid=entry.user_uuid,
                reference=entry.reference,
            )
        )

    outbound_rows = session.exec(select(StockExit, SKU).join(SKU, StockExit.sku_id == SKU.id)).all()
    for stock_exit, sku in outbound_rows:
        movement_rows.append(
            InventoryMovementRead(
                id=stock_exit.id,
                movement_type="outbound",
                sku_id=stock_exit.sku_id,
                sku=sku.sku,
                sku_name=sku.name,
                client_name=sku.client_name,
                category=sku.category,
                quantity=stock_exit.quantity,
                warehouse=stock_exit.warehouse,
                created_at=stock_exit.created_at,
                user_uuid=stock_exit.user_uuid,
                exit_type=stock_exit.exit_type,
                tracking_number=stock_exit.tracking_number,
            )
        )

    return sorted(movement_rows, key=lambda item: item.created_at, reverse=True)


def _sku_or_404(session: Session, sku_id: int) -> SKU:
    sku = session.get(SKU, sku_id)
    if sku is None:
        raise HTTPException(status_code=404, detail="SKU not found.")
    return sku


@router.get("/products", response_model=list[SKURead])
def list_products(
    session: Annotated[Session, Depends(get_sql_session)],
    current_user: Annotated[UserPublic, Depends(get_current_user)],
) -> list[SKURead]:
    _ = current_user
    cached = cache_get(INVENTORY_PRODUCTS_KEY)
    if cached is not None:
        return [SKURead.model_validate(item) for item in cached]

    products = _build_product_reads(session)
    cache_set(
        INVENTORY_PRODUCTS_KEY,
        [product.model_dump(mode="json") for product in products],
        PRODUCTS_CACHE_TTL_SECONDS,
    )
    return products


@router.post("/products", response_model=SKURead, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: SKUCreate,
    session: Annotated[Session, Depends(get_sql_session)],
    current_user: Annotated[UserPublic, Depends(get_current_user)],
) -> SKURead:
    _ = current_user
    sku = SKU.model_validate(payload)
    session.add(sku)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail="SKU already exists for this warehouse.") from exc

    session.refresh(sku)
    _invalidate_inventory_cache()
    return SKURead(
        id=sku.id,
        name=sku.name,
        sku=sku.sku,
        client_name=sku.client_name,
        category=sku.category,
        warehouse=sku.warehouse,
        current_stock=0,
    )


@router.get("/products/{product_id}", response_model=SKURead)
def get_product(
    product_id: int,
    session: Annotated[Session, Depends(get_sql_session)],
    current_user: Annotated[UserPublic, Depends(get_current_user)],
) -> SKURead:
    _ = current_user
    sku = _sku_or_404(session, product_id)
    return SKURead(
        id=sku.id,
        name=sku.name,
        sku=sku.sku,
        client_name=sku.client_name,
        category=sku.category,
        warehouse=sku.warehouse,
        current_stock=_compute_current_stock(session, sku.id, sku.warehouse),
    )


@router.post("/orders/inbound", response_model=StockEntryRead, status_code=status.HTTP_201_CREATED)
def register_inbound_order(
    payload: StockEntryCreate,
    session: Annotated[Session, Depends(get_sql_session)],
    current_user: Annotated[UserPublic, Depends(get_current_user)],
) -> StockEntryRead:
    sku = _sku_or_404(session, payload.sku_id)
    if sku.warehouse != payload.warehouse:
        raise HTTPException(status_code=400, detail="SKU warehouse must match stock movement warehouse.")

    stock_entry = StockEntry(
        sku_id=payload.sku_id,
        quantity=payload.quantity,
        reference=payload.reference,
        warehouse=payload.warehouse,
        user_uuid=current_user.user_uuid,
    )
    session.add(stock_entry)
    session.commit()
    session.refresh(stock_entry)
    _invalidate_inventory_cache()
    return StockEntryRead.model_validate(stock_entry)


@router.post("/orders/outbound", response_model=StockExitRead, status_code=status.HTTP_201_CREATED)
def register_outbound_order(
    payload: StockExitCreate,
    session: Annotated[Session, Depends(get_sql_session)],
    current_user: Annotated[UserPublic, Depends(get_current_user)],
) -> StockExitRead:
    sku = _sku_or_404(session, payload.sku_id)
    if sku.warehouse != payload.warehouse:
        raise HTTPException(status_code=400, detail="SKU warehouse must match stock movement warehouse.")

    available = _compute_current_stock(session, payload.sku_id, payload.warehouse)
    if payload.quantity > available:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Insufficient stock for SKU '{sku.sku}'. "
                f"Available: {available}, requested: {payload.quantity}."
            ),
        )

    stock_exit = StockExit(
        sku_id=payload.sku_id,
        quantity=payload.quantity,
        exit_type=payload.exit_type,
        tracking_number=payload.tracking_number,
        warehouse=payload.warehouse,
        user_uuid=current_user.user_uuid,
    )
    session.add(stock_exit)
    session.commit()
    session.refresh(stock_exit)
    _invalidate_inventory_cache()
    return StockExitRead.model_validate(stock_exit)


@router.get("/orders", response_model=list[InventoryMovementRead])
def list_orders(
    session: Annotated[Session, Depends(get_sql_session)],
    current_user: Annotated[UserPublic, Depends(get_current_user)],
) -> list[InventoryMovementRead]:
    _ = current_user

    cached = cache_get(INVENTORY_ORDERS_KEY)
    if cached is not None:
        return [InventoryMovementRead.model_validate(item) for item in cached]

    orders = _build_order_reads(session)
    cache_set(
        INVENTORY_ORDERS_KEY,
        [order.model_dump(mode="json") for order in orders],
        ORDERS_CACHE_TTL_SECONDS,
    )
    return orders
