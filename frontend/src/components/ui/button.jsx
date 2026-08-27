import * as React from "react"
import { cn } from "../../lib/utils"

const Button = React.forwardRef(({ className, variant = "default", size = "default", ...props }, ref) => {
  return (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center rounded-full text-sm font-medium ring-offset-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
        {
          "bg-black text-white hover:bg-black/90": variant === "default",
          "bg-red-500 text-white hover:bg-red-500/90": variant === "destructive",
          "border border-gray-200 bg-white hover:bg-gray-100 hover:text-black": variant === "outline",
          "hover:bg-gray-100 hover:text-black": variant === "ghost",
          "bg-gray-100 text-black hover:bg-gray-200/80": variant === "secondary",
        },
        {
          "h-10 px-4 py-2": size === "default",
          "h-9 px-3": size === "sm",
          "h-11 px-8": size === "lg",
          "h-10 w-10": size === "icon",
        },
        className
      )}
      {...props}
    />
  )
})
Button.displayName = "Button"

export { Button }
