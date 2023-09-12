import copy


def get_forms(soup):
    """Returns parsed page forms"""
    allowed_elements = ["form", "input", "select", "textarea", "label", "button", "datalist", "output"]
    forms = soup.find_all("form")
    forms_result = []
    for form in forms:
        form_elements = strip_form_elements(form.find_all(allowed_elements))
        forms_result.append({"form_name": form.get("name"), "action": form.get("action"), "method": form.get("method"), "form_id": form.get("id"),
        "inputs": [{"tag": ele.name, **ele.attrs} for ele in form_elements["inputs"]], "selects": [{"tag": ele.name, **ele.attrs} for ele in form_elements["selects"]]})
    return forms_result


def pop_value_key_from_form(form):
    """returns form without keys named 'value' (csrf tokens)"""
    form = copy.deepcopy(form)
    if form.get("inputs"):
        for parsed_input in form["inputs"]:
            if "value" in parsed_input.keys():
                parsed_input.pop("value")
    return form


def strip_form_elements(form_elements):
    """strip child elements of parent element"""
    allowed_attrs = ("name", "type", "id", "value")
    result = {"inputs": [], "selects": []}
    for element in form_elements:
        element.attrs = {key: value for key, value in element.attrs.items() if key in allowed_attrs}
        if element.name == "select":
            element.attrs.update({"options": []})
        children = element.findChildren(True, recursive=True)
        for child in children:
            if child.name == "option":
                element.attrs["options"].append(child.get("value", "notfound"))
            else:
                child.unwrap()
        if element.name == "select":
            result["selects"].append(element)
        else:
            result["inputs"].append(element)
    return result