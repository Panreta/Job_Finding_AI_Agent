def assemble_tex(template: dict, tailored_sections: dict) -> str:
    """
    Take main.tex as the skeleton, replace \\input{section.tex}
    with the tailored content for each section.
    """
    main_tex = template.get("main.tex", "")

    if not main_tex:
        parts = []
        for section_name, data in tailored_sections.items():
            parts.append(f"% --- {section_name} ---")
            parts.append(data["latex"])
        return "\n\n".join(parts)

    # Use plain string replace — NO regex anywhere
    result = main_tex
    for section_name, data in tailored_sections.items():
        filename = data["filename"]
        bare_name = filename.replace(".tex", "")
        replacement = f"% --- {section_name} (tailored) ---\n{data['latex']}"

        # Try both formats: \input{name} and \input{name.tex}
        old1 = f"\\input{{{bare_name}}}"
        old2 = f"\\input{{{bare_name}.tex}}"

        if old1 in result:
            result = result.replace(old1, replacement)
        elif old2 in result:
            result = result.replace(old2, replacement)
        else:
            # Section not found in main.tex, append it
            print(f"  [WARN] \\input{{{bare_name}}} not found in main.tex, appending")
            result += f"\n\n{replacement}\n"

    return result