interface ViewProps {
  hidden?: boolean;
}

export function MissionsView({ hidden }: ViewProps) {
  return <section hidden={hidden} />;
}
