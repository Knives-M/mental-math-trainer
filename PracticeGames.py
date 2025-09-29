from flask import Blueprint, session, redirect, url_for

practice_bp = Blueprint("practice", __name__, template_folder="templates")

# 🔑 Mapping for hacks → rules
mapping = {
    # ➕ Addition
    "add2digit": {"a_digits": 2, "b_digits": 2, "op": "+", "n": 10},
    "add3digit": {"a_digits": 3, "b_digits": 3, "op": "+", "n": 10},

    # ➖ Subtraction
    "sub2digit": {"a_digits": 2, "b_digits": 2, "op": "-", "n": 10},
    "sub2digit_comp": {"a_digits": 2, "b_digits": 2, "op": "-", "n": 10},
    "sub3digit": {"a_digits": 3, "b_digits": 3, "op": "-", "n": 10},

    # ✖ Multiplication
    "mult11": {"a_digits": 2, "b_fixed": 11, "op": "*", "n": 10},
    "mult2x1": {"a_digits": 2, "b_digits": 1, "op": "*", "n": 10},
    "mult5": {"a_digits": 2, "b_fixed": 5, "op": "*", "n": 10},

    # ➗ Division
    "div5": {"a_digits": 3, "b_fixed": 5, "op": "/", "n": 10},
}


@practice_bp.route("/practice/<hack_id>")
def start_practice(hack_id):
    entry = mapping.get(hack_id)
    if entry is None:
        # default fallback
        entry = {"a_digits": 2, "b_digits": 1, "op": "+", "n": 10}

    # Store in session
    session["a_digits"] = entry.get("a_digits")
    session["b_digits"] = entry.get("b_digits")
    session["a_fixed"] = entry.get("a_fixed")
    session["b_fixed"] = entry.get("b_fixed")
    session["c"] = entry["op"]
    session["n"] = entry["n"]
    session["current_index"] = 0

    session.pop("current_problem", None)
    session.pop("previous_pair", None)

    return redirect(url_for("game"))
