import type { SVGProps } from 'react'

export function SailMark({
  className = '',
  'aria-hidden': ariaHidden = true,
  ...props
}: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 256 256"
      className={className}
      aria-hidden={ariaHidden}
      {...props}
    >
      {/* Sail */}
      <path
        d="M96 20 L96 200 L196 200 Q188 108 96 20Z"
        className="fill-zone-calendar"
      />
      {/* Mast */}
      <line
        x1="96" y1="14" x2="96" y2="208"
        stroke="currentColor"
        strokeWidth="8"
        strokeLinecap="round"
      />
      {/* Hull */}
      <path
        d="M48 218 Q96 250 196 218"
        stroke="currentColor"
        strokeWidth="8"
        fill="none"
        strokeLinecap="round"
      />
    </svg>
  )
}
