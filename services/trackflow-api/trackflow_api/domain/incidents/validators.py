def validate_incident_row(row: dict[str, str], config: dict) -> tuple[list[str], int | None]:
    reasons: list[str] = []
    parsed_score: int | None = None

    required_fields = config["required_fields"]
    for field in required_fields:
        if field in {
            config["tracking_number_field"],
            config["category_field"],
            config["description_field"],
            config["customer_email_field"],
            config["country_field"],
            config["carrier_field"],
            config["status_field"],
        }:
            continue
        if not row.get(field, ""):
            reasons.append(f"missing_required_field:{field}")

    country = row.get(config["country_field"], "")
    if not country or country not in config["allowed_countries"]:
        reasons.append("invalid_country")

    tracking_number = row.get(config["tracking_number_field"], "")
    min_length = int(config.get("tracking_number_min_length", 8))
    if not tracking_number or len(tracking_number) < min_length:
        reasons.append("invalid_tracking_number")

    carrier = row.get(config["carrier_field"], "")
    carriers_by_country = config.get("carriers_by_country", {})
    if country in config["allowed_countries"]:
        allowed_carriers = set(carriers_by_country.get(country, []))
        if not carrier or carrier not in allowed_carriers:
            reasons.append("carrier_country_mismatch")
    elif not carrier:
        reasons.append("carrier_country_mismatch")

    category = row.get(config["category_field"], "")
    if not category or category not in config["allowed_categories"]:
        reasons.append("invalid_category")

    description = row.get(config["description_field"], "")
    min_description = int(config.get("description_min_length", 5))
    if not description or len(description) < min_description:
        reasons.append("invalid_description")

    email = row.get(config["customer_email_field"], "")
    if not email or "@" not in email:
        reasons.append("invalid_email")

    status = row.get(config["status_field"], "")
    if not status or status not in config["allowed_statuses"]:
        reasons.append("invalid_status")

    satisfaction_value = row.get(config["satisfaction_field"], "")
    if satisfaction_value:
        try:
            parsed_score = int(satisfaction_value)
        except ValueError:
            reasons.append("invalid_satisfaction_score")
        else:
            score_min = int(config.get("satisfaction_score_min", 1))
            score_max = int(config.get("satisfaction_score_max", 5))
            if parsed_score < score_min or parsed_score > score_max:
                reasons.append("invalid_satisfaction_score")

    if status in config["closed_statuses"] and not satisfaction_value:
        reasons.append("closed_without_score")

    return reasons, parsed_score if satisfaction_value and "invalid_satisfaction_score" not in reasons else None
