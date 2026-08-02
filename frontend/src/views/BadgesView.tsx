interface ViewProps {
  hidden?: boolean;
}

export function BadgesView({ hidden }: ViewProps) {
  return <section hidden={hidden} />;
}
