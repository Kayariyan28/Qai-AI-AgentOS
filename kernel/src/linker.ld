ENTRY(_start)

SECTIONS {
    . = 2M;

    .text :
    {
        *(.text .text.*)
    }

    .rodata :
    {
        *(.rodata .rodata.*)
    }

    .data :
    {
        *(.data .data.*)
    }

    .bss :
    {
        *(.bss .bss.*)
    }
}
