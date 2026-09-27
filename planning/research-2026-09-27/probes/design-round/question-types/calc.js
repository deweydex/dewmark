const CALC_FUNCTIONS = {
  sqrt: Math.sqrt,
  sin: Math.sin, cos: Math.cos, tan: Math.tan,
  asin: Math.asin, acos: Math.acos, atan: Math.atan,
  sind: (d) => Math.sin(d * Math.PI / 180),
  cosd: (d) => Math.cos(d * Math.PI / 180),
  tand: (d) => Math.tan(d * Math.PI / 180),
  asind: (x) => Math.asin(x) * 180 / Math.PI,
  acosd: (x) => Math.acos(x) * 180 / Math.PI,
  atand: (x) => Math.atan(x) * 180 / Math.PI,
};

function calculate(text) {
  /* Returns a number, or throws with a readable message. */
  const source = text.replace(/÷/g, "/").replace(/×/g, "*")
    .replace(/−/g, "-").replace(/√/g, "sqrt").replace(/π/g, "pi");
  const tokens = [];
  const tokenRe = /\s*(?:(\d+\.?\d*|\.\d+)|([A-Za-z]+)|([()+\-*/^]))/y;
  let at = 0;
  while (at < source.length) {
    tokenRe.lastIndex = at;
    const match = tokenRe.exec(source);
    if (!match || tokenRe.lastIndex === at) {
      if (!source.slice(at).trim()) break;
      throw new Error("cannot read “" + source.slice(at).trim()
        + "”");
    }
    if (match[1] !== undefined) tokens.push(Number(match[1]));
    else tokens.push(match[2] || match[3]);
    at = tokenRe.lastIndex;
  }
  if (!tokens.length) throw new Error("nothing to work out");

  let position = 0;
  const peek = () => tokens[position];
  const take = () => tokens[position++];

  function primary() {
    const token = take();
    if (typeof token === "number") return token;
    if (token === "pi") return Math.PI;
    if (token === "(") {
      const value = sum();
      if (take() !== ")") throw new Error("a bracket is not closed");
      return value;
    }
    if (token === "-") return -primary();
    if (token === "+") return primary();
    if (CALC_FUNCTIONS[token]) {
      if (take() !== "(") {
        throw new Error(token + " needs brackets: " + token + "(...)");
      }
      const value = sum();
      if (take() !== ")") throw new Error("a bracket is not closed");
      return CALC_FUNCTIONS[token](value);
    }
    throw new Error("cannot read “" + token + "”");
  }

  function power() {
    const base = primary();
    if (peek() === "^") { take(); return base ** power(); }
    return base;
  }

  function product() {
    let value = power();
    while (peek() === "*" || peek() === "/") {
      value = take() === "*" ? value * power() : value / power();
    }
    return value;
  }

  function sum() {
    let value = product();
    while (peek() === "+" || peek() === "-") {
      value = take() === "+" ? value + product() : value - product();
    }
    return value;
  }

  const result = sum();
  if (position < tokens.length) {
    throw new Error("cannot read “" + tokens[position] + "”");
  }
  if (!Number.isFinite(result)) throw new Error("this has no value");
  return result;
}

const tries = ["3", "11", "2*sqrt(13)", "2sqrt(13)", "2√13", "3/13", "sqrt(3)/3", "1/sqrt(3)",
  "10^4", "10,000", "5,040", "5040", "1/10000", "(1/2)^8", "95.9°", "95.9", "22.5 cm²", "22.5",
  "-1/2", "−12", "5.0 × 10^2", "5e2", "x = 4", "0.5", "1/2 × 1/2 × 1/2", "3.9"];
for (const t of tries) {
  try { console.log(JSON.stringify(t).padEnd(16), "=>", calculate(t)); }
  catch (e) { console.log(JSON.stringify(t).padEnd(16), "=> cannot read:", e.message); }
}
