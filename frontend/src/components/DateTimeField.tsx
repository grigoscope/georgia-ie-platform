type DateTimeFieldProps = {
  value: string
  onChange: (
    value: string,
  ) => void
}

export function DateTimeField({
  value,
  onChange,
}: DateTimeFieldProps) {
  const [
    date,
    time = '12:00',
  ] = value.split('T')

  return (
    <>
      <label>
        Дата получения

        <input
          type="date"
          lang="ru"
          value={date}
          onChange={(event) => {
            onChange(
              `${event.target.value}T${time}`,
            )
          }}
          required
        />
      </label>

      <label>
        Время получения

        <input
          type="time"
          lang="ru"
          value={time}
          onChange={(event) => {
            onChange(
              `${date}T${event.target.value}`,
            )
          }}
          required
        />
      </label>
    </>
  )
}