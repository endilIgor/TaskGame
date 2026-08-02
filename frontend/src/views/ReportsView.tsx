interface ViewProps {
  hidden?: boolean;
}

export function ReportsView({ hidden }: ViewProps) {
  return <section hidden={hidden} />;
}
