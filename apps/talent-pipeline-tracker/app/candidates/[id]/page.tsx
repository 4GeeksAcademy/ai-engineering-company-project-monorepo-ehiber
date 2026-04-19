import { CandidateDetailPage } from "@/components/candidate-detail-page";

export default async function CandidatePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return <CandidateDetailPage candidateId={id} />;
}
