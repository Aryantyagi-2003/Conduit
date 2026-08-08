/** Purely decorative: faint layered horizon arcs behind the masthead,
 * suggesting altitude/atmosphere without a literal sun or cloud icon.
 * aria-hidden, no data, no interaction.
 */
export function Atmosphere() {
  return (
    <svg
      viewBox="0 0 800 200"
      preserveAspectRatio="none"
      aria-hidden
      className="pointer-events-none absolute inset-0 h-full w-full"
    >
      <path
        d="M -20 150 Q 200 100 400 130 T 820 110"
        fill="none"
        stroke="var(--color-accent)"
        strokeOpacity="0.10"
        strokeWidth="1"
      />
      <path
        d="M -20 175 Q 220 140 420 160 T 820 145"
        fill="none"
        stroke="var(--color-warm)"
        strokeOpacity="0.14"
        strokeWidth="1"
      />
      <path
        d="M -20 195 Q 240 175 440 185 T 820 175"
        fill="none"
        stroke="var(--color-accent)"
        strokeOpacity="0.08"
        strokeWidth="1"
      />
    </svg>
  );
}
