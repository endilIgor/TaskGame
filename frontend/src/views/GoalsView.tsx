interface ViewProps {
  hidden?: boolean;
}

export function GoalsView({ hidden }: ViewProps) {
  return <section hidden={hidden} />;
}
