








"Project: {name}\nScan: {scan_id}\n{body}"

# caller
text = get_text_template().format(
    name=project_name,
    scan_id=scan_id,
    body=ascii_tree_str,
)