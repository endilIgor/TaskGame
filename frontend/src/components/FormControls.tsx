import { Children, isValidElement, useEffect, useId, useMemo, useRef, useState } from "react";
import type { InputHTMLAttributes, OptionHTMLAttributes, ReactElement, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from "react";
import { GameIcon } from "./GameIcon";

interface FieldProps {
  label: string;
  children: ReactNode;
  className?: string;
  hint?: string;
}

export function FormField({ label, children, className = "", hint }: FieldProps) {
  return <label className={`form-field ${className}`.trim()}><span className="field-label">{label}</span>{children}{hint ? <span className="field-hint">{hint}</span> : null}</label>;
}

export function TextInput(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} />;
}

interface DatePickerProps {
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  min?: string;
  max?: string;
  "aria-label"?: string;
}

function formatDateDisplay(value: string): string {
  if (!value) return "dd/mm/aaaa";
  const [year, month, day] = value.split("-");
  if (!year || !month || !day) return value;
  return `${day}/${month}/${year}`;
}

function formatMonthDisplay(value: string): string {
  if (!value) return "mm/aaaa";
  const [year, month] = value.split("-");
  if (!year || !month) return value;
  return `${month}/${year}`;
}

export function DateInput({ value, onChange, required, min, max, "aria-label": ariaLabel }: DatePickerProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const openPicker = () => {
    const input = inputRef.current;
    if (!input) return;
    input.focus();
    input.showPicker?.();
  };

  return (
    <span className="calendar-display-control">
      <span className={`calendar-display-value${value ? "" : " placeholder"}`}>{formatDateDisplay(value)}</span>
      <button className="calendar-picker-button" type="button" aria-label={ariaLabel ?? "Abrir calendário"} onClick={openPicker}><GameIcon variant="calendar" /></button>
      <input ref={inputRef} className="calendar-native-input" type="date" lang="pt-BR" tabIndex={-1} required={required} min={min} max={max} value={value} aria-hidden="true" onChange={(event) => onChange(event.target.value)} />
    </span>
  );
}

export function MonthInput({ value, onChange, required, min, max, "aria-label": ariaLabel }: DatePickerProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const openPicker = () => {
    const input = inputRef.current;
    if (!input) return;
    input.focus();
    input.showPicker?.();
  };

  return (
    <span className="calendar-display-control">
      <span className={`calendar-display-value${value ? "" : " placeholder"}`}>{formatMonthDisplay(value)}</span>
      <button className="calendar-picker-button" type="button" aria-label={ariaLabel ?? "Abrir calendário de mês"} onClick={openPicker}><GameIcon variant="calendar" /></button>
      <input ref={inputRef} className="calendar-native-input" type="month" lang="pt-BR" tabIndex={-1} required={required} min={min} max={max} value={value} aria-hidden="true" onChange={(event) => onChange(event.target.value)} />
    </span>
  );
}

type SelectOption = {
  value: string;
  label: string;
  disabled: boolean;
};

function optionText(children: ReactNode): string {
  return Children.toArray(children).map((child) => typeof child === "string" || typeof child === "number" ? String(child) : "").join("");
}

export function SelectInput({ children, value, defaultValue, onChange, disabled, "aria-label": ariaLabel }: SelectHTMLAttributes<HTMLSelectElement>) {
  const generatedId = useId();
  const containerRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const options = useMemo<SelectOption[]>(() => Children.toArray(children).flatMap((child) => {
    if (!isValidElement(child) || child.type !== "option") return [];
    const option = child as ReactElement<OptionHTMLAttributes<HTMLOptionElement>>;
    const rawValue = option.props.value;
    return [{
      value: rawValue === undefined ? optionText(option.props.children) : String(rawValue),
      label: optionText(option.props.children),
      disabled: Boolean(option.props.disabled),
    }];
  }), [children]);
  const selectedValue = String(value ?? defaultValue ?? options[0]?.value ?? "");
  const selectedOption = options.find((option) => option.value === selectedValue) ?? options[0];

  useEffect(() => {
    if (!open) return;
    function closeOnOutsideClick(event: PointerEvent) {
      if (!containerRef.current?.contains(event.target as Node)) setOpen(false);
    }
    window.addEventListener("pointerdown", closeOnOutsideClick);
    return () => window.removeEventListener("pointerdown", closeOnOutsideClick);
  }, [open]);

  function selectValue(nextValue: string) {
    onChange?.({ target: { value: nextValue }, currentTarget: { value: nextValue } } as unknown as React.ChangeEvent<HTMLSelectElement>);
    setOpen(false);
  }

  return (
    <div className={`custom-select${open ? " open" : ""}${disabled ? " disabled" : ""}`} ref={containerRef}>
      <button
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-label={ariaLabel}
        className="custom-select-trigger"
        disabled={disabled}
        id={generatedId}
        type="button"
        onClick={(event) => {
          event.preventDefault();
          event.stopPropagation();
          setOpen((current) => !current);
        }}
        onKeyDown={(event) => {
          if (event.key === "Escape") setOpen(false);
          if (event.key === "ArrowDown" || event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            setOpen(true);
          }
        }}
      >
        <span>{selectedOption?.label ?? "Selecione"}</span>
        <span className="custom-select-chevron" aria-hidden="true">⌄</span>
      </button>
      {open ? (
        <div className="custom-select-menu" role="listbox" aria-labelledby={generatedId}>
          {options.map((option) => (
            <button
              aria-selected={option.value === selectedValue}
              className={`custom-select-option${option.value === selectedValue ? " selected" : ""}`}
              disabled={option.disabled}
              key={option.value}
              role="option"
              type="button"
              onClick={(event) => {
                event.preventDefault();
                event.stopPropagation();
                selectValue(option.value);
              }}
            >
              {option.label}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}

export function TextArea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...props} />;
}
