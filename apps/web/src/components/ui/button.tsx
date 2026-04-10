import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-full border text-sm font-semibold transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 ring-offset-background",
  {
    variants: {
      variant: {
        default:
          "border-primary/80 bg-primary px-5 py-2.5 text-primary-foreground shadow-[0_14px_30px_rgba(16,66,91,0.18)] hover:-translate-y-0.5 hover:bg-primary/95 hover:shadow-[0_20px_34px_rgba(16,66,91,0.22)]",
        secondary:
          "border-white/70 bg-white/70 px-5 py-2.5 text-secondary-foreground shadow-[0_10px_26px_rgba(53,47,35,0.08)] backdrop-blur hover:-translate-y-0.5 hover:bg-white",
        ghost:
          "border-transparent bg-transparent px-4 py-2 text-foreground/80 hover:border-border hover:bg-white/70 hover:text-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return <Comp className={cn(buttonVariants({ variant, className }))} ref={ref} {...props} />;
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
