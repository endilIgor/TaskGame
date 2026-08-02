interface ViewProps {
  hidden?: boolean;
}

export function RewardsView({ hidden }: ViewProps) {
  return <section hidden={hidden} />;
}
