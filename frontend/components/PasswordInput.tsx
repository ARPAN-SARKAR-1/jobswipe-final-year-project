"use client";

import { Eye, EyeOff } from "lucide-react";
import { forwardRef, type InputHTMLAttributes, useState } from "react";

import { cx } from "@/lib/utils";

type PasswordInputProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type">;

const PasswordInput = forwardRef<HTMLInputElement, PasswordInputProps>(function PasswordInput(
  { className, disabled, ...props },
  ref
) {
  const [visible, setVisible] = useState(false);
  const label = visible ? "Hide password" : "Show password";

  return (
    <div className="relative">
      <input
        {...props}
        ref={ref}
        className={cx("field pr-12", className)}
        disabled={disabled}
        type={visible ? "text" : "password"}
      />
      <button
        aria-label={label}
        className="absolute right-2 top-1/2 grid h-9 w-9 -translate-y-1/2 place-items-center rounded-md text-[#526069] transition hover:bg-black/5 hover:text-[#172026] focus:outline-none focus:ring-2 focus:ring-teal-500 disabled:cursor-not-allowed disabled:opacity-50"
        disabled={disabled}
        onClick={() => setVisible((value) => !value)}
        type="button"
      >
        {visible ? <EyeOff aria-hidden="true" size={18} /> : <Eye aria-hidden="true" size={18} />}
      </button>
    </div>
  );
});

export default PasswordInput;
