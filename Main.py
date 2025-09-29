# Import necessary modules
from flask import Flask, render_template, request, redirect, url_for, session, os
from PracticeGames import practice_bp
import random  # random number generation

# ------------------- Flask App Setup -------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-insecure")  # change to a secure value in production

# Register blueprint for practice mode
app.register_blueprint(practice_bp)


# ------------------- Helpers -------------------
def digits_range(d):
    """Return (min_val, max_val) for an integer with `d` digits."""
    if d <= 1:
        return 1, 9
    return 10 ** (d - 1), 10 ** d - 1


def division_feasible(a_digits, b_digits):
    """
    Check if it's possible to generate division problems with:
      - b != 1
      - quotient (d) >= 2
      - and a having a_digits digits
    """
    a_min, a_max = digits_range(a_digits)
    b_min, b_max = digits_range(b_digits)
    b_min = max(2, b_min)  # disallow b == 1

    # If b-range small, iterate all; otherwise sample
    full_size = b_max - b_min + 1
    if full_size <= 10000:
        candidates = range(b_min, b_max + 1)
    else:
        candidates = (random.randint(b_min, b_max) for _ in range(500))

    for b in candidates:
        min_mul = (a_min + b - 1) // b
        max_mul = a_max // b
        if max_mul >= max(2, min_mul):
            return True
    return False


# ------------------- Problem Generator -------------------
def generate_problem_on_the_spot(a_digits, b_digits, op):
    """
    Generate one problem (a, b, op, d).
    Supports fixed a or b values from session (overrides digit-based random).
    """
    a_fixed = session.get("a_fixed")
    b_fixed = session.get("b_fixed")

    a, b = a_fixed, b_fixed

    # --- Pick a if not fixed ---
    if a is None:
        if a_digits is not None:
            a_min, a_max = digits_range(a_digits)
            a = random.randint(a_min, a_max)
        else:
            a = random.randint(1, 99)

    # --- Pick b if not fixed ---
    if b is None:
        if b_digits is not None:
            b_min, b_max = digits_range(b_digits)
            b = random.randint(b_min, b_max)
        else:
            b = random.randint(1, 9)

    # --- Handle operations ---
    if op == "+":
        return a, b, "+", a + b

    elif op == "-":
        # ensure b < a
        if b >= a:
            if b_digits is not None:
                _, b_max = digits_range(b_digits)
                b = random.randint(1, min(b_max, a - 1))
            else:
                b = random.randint(1, a - 1)
        return a, b, "-", a - b

    elif op == "*":
        return a, b, "*", a * b

    elif op == "/":
        # If b is fixed (like ÷5 hack), enforce clean division
        if session.get("b_fixed") is not None:
            if b in (0, 1):
                b = 2
            a = b * random.randint(2, 20)
            return a, b, "/", a // b

        # Otherwise generate random clean division
        b_min = 2 if not b_digits else digits_range(b_digits)[0]
        b_max = 9 if not b_digits else digits_range(b_digits)[1]
        for _ in range(300):
            b = random.randint(b_min, b_max)
            if a_digits:
                a_min, a_max = digits_range(a_digits)
            else:
                a_min, a_max = (10, 999)
            min_mul = (a_min + b - 1) // b
            max_mul = a_max // b
            if max_mul >= max(2, min_mul):
                m = random.randint(max(2, min_mul), max_mul)
                a = b * m
                return a, b, "/", a // b

        # fallback
        b = 2
        a = 2 * b
        return a, b, "/", a // b

    # default fallback
    return a, b, op, None


# ------------------- Setup Page -------------------
@app.route("/", methods=["GET", "POST"])
def setup():
    """
    Setup form: collects a_digits, b_digits, operation c, and n.
    Validates rules for subtraction/division.
    """
    if request.method == "POST":
        a_digits = max(1, min(8, int(request.form.get("digits_a", 1))))
        b_digits = max(1, min(8, int(request.form.get("digits_b", 1))))
        c = request.form.get("c", "+")
        n = int(request.form.get("n", 1))
        n = max(1, min(1000, n))

        # validation
        if c in ("-", "/") and b_digits > a_digits:
            error = "For subtraction and division, b's digits cannot be greater than a's."
            return render_template("setup.html", error=error)

        if c == "-":
            a_min, a_max = digits_range(a_digits)
            b_min, b_max = digits_range(b_digits)
            if a_max <= b_min:
                error = "Impossible to guarantee b < a with these digits."
                return render_template("setup.html", error=error)

        if c == "/":
            if not division_feasible(a_digits, b_digits):
                error = "These digit ranges can't produce valid division problems."
                return render_template("setup.html", error=error)

        # save criteria
        session["a_digits"] = a_digits
        session["b_digits"] = b_digits
        session["c"] = c
        session["n"] = n
        session["current_index"] = 0
        session.pop("current_problem", None)
        session.pop("previous_pair", None)

        return redirect(url_for("game"))

    return render_template("setup.html")


# ------------------- Game Page -------------------
@app.route("/game", methods=["GET", "POST"], endpoint="game")
def game():
    required = ("a_digits", "b_digits", "c", "n", "current_index")
    if not all(k in session for k in required):
        return redirect(url_for("setup"))

    a_digits = session["a_digits"]
    b_digits = session["b_digits"]
    op = session["c"]
    n = session["n"]
    idx = session.get("current_index", 0)

    # POST
    if request.method == "POST":
        if "abort" in request.form:
            session.clear()
            return redirect(url_for("setup"))

        user_input = request.form.get("d", "").strip()
        try:
            user_val = int(user_input)
        except (ValueError, TypeError):
            user_val = None

        cur = session.get("current_problem")
        if cur and user_val is not None:
            correct = cur[3]
            if user_val == correct:
                session["previous_pair"] = (cur[0], cur[1])
                idx += 1
                session["current_index"] = idx
                session.pop("current_problem", None)
                if idx >= n:
                    session.clear()
                    return redirect(url_for("setup"))
        return redirect(url_for("game"))

    # GET
    if "current_problem" not in session:
        prev = session.get("previous_pair")
        attempts = 0
        candidate = None
        while True:
            attempts += 1
            candidate = generate_problem_on_the_spot(a_digits, b_digits, op)
            a_c, b_c, op_c, d_c = candidate
            if not prev or (a_c, b_c) != prev:
                break
            if attempts >= 300:
                break
        session["current_problem"] = candidate

    a, b, op_c, correct_answer = session["current_problem"]
    return render_template(
        "game.html",
        a=a, b=b, c=op_c,
        current_index=idx + 1, total=n,
        correct_answer=correct_answer
    )


# ------------------- Hack Explanations -------------------
hack_explanations = {
    "add2digit": "When adding 2-digit numbers, split them into tens and ones. Example: 47+36 = (40+30)+(7+6).",
    "add3digit": "For 3-digit numbers, add hundreds, tens, and ones separately.",
    "sub2digit": "Subtract tens and then ones, borrowing if needed.",
    "sub2digit_comp": "Compensation strategy: Adjust numbers to make subtraction easier.",
    "sub3digit": "Subtract hundreds, tens, and ones separately with borrowing when required.",
    "mult11": "To multiply a 2-digit number by 11, add the digits and put the result in the middle.",
    "mult2x1": "Break a 2-digit number into tens and ones, then multiply each by the 1-digit number.",
    "mult5": "Multiply by 10 and divide by 2 to quickly calculate ×5.",
    "div5": "To divide by 5, double the number and then divide by 10."
}


@app.route("/hacks")
def hacks():
    return render_template("hacks.html")


@app.route("/explainer/<hack_id>")
def explainer(hack_id):
    explanation = hack_explanations.get(hack_id, "No explanation found for this hack.")
    return render_template("explainer.html", hack_id=hack_id, explanation=explanation)


# ------------------- Run Flask -------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
