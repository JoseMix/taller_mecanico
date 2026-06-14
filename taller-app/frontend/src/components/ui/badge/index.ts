import type { VariantProps } from "class-variance-authority"
import { cva } from "class-variance-authority"

export { default as Badge } from "./Badge.vue"

export const badgeVariants = cva(
  'h-5 gap-1 rounded-full border border-transparent px-2 py-0.5 text-xs font-medium transition-all has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5 [&>svg]:size-3! group/badge inline-flex w-fit shrink-0 items-center justify-center overflow-hidden whitespace-nowrap focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 aria-invalid:border-destructive aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 [&>svg]:pointer-events-none',
  {
    variants: {
      variant: {
        // Default — usa el primary (cyan)
        default:
          'bg-primary/15 text-primary border-primary/30 dark:bg-primary/20 dark:text-primary',

        // Secondary — slate discreto
        secondary:
          'bg-secondary text-secondary-foreground [a]:hover:bg-secondary/80',

        // Destructive — rojo visible
        destructive:
          'bg-destructive/15 text-destructive border-destructive/40 dark:bg-destructive/20 dark:text-red-400',

        // Outline genérico
        outline:
          'border-border text-foreground [a]:hover:bg-muted [a]:hover:text-muted-foreground',

        // Ghost
        ghost:
          'hover:bg-muted hover:text-muted-foreground dark:hover:bg-muted/50',

        // Link
        link: 'text-primary underline-offset-4 hover:underline',

        /* ── Variantes semánticas para estados de órdenes ── */

        // Recibida — slate/neutral
        recibida:
          'bg-slate-500/15 text-slate-300 border-slate-500/30 dark:bg-slate-700/30',

        // Presupuestado — azul cielo
        presupuestado:
          'bg-sky-500/15 text-sky-300 border-sky-500/35 dark:bg-sky-500/20',

        // En Reparación — cyan brillante (el estado más activo)
        enreparacion:
          'bg-cyan-500/20 text-cyan-300 border-cyan-400/40 dark:bg-cyan-400/20 font-semibold tracking-wide',

        // Finalizada — ámbar/dorado
        finalizada:
          'bg-amber-500/15 text-amber-300 border-amber-400/35 dark:bg-amber-500/20',

        // Entregado — verde
        entregado:
          'bg-emerald-500/15 text-emerald-300 border-emerald-500/35 dark:bg-emerald-500/20',

        // Rechazado — rojo
        rechazado:
          'bg-red-500/15 text-red-400 border-red-500/40 dark:bg-red-500/20',
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
)
export type BadgeVariants = VariantProps<typeof badgeVariants>
