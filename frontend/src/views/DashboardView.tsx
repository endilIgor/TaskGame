interface ViewProps {
  hidden?: boolean;
}

export function DashboardView({ hidden }: ViewProps) {
  return <section hidden={hidden} />;
}
