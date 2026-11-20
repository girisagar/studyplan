#!/usr/bin/env python3
"""
Builds initial.json, a Django fixture that seeds the curriculum, library and
roadmaps apps with six study roadmaps for an ML quant engineer path.

Structure: one Roadmap made of six Courses (RoadMapCourse rows, run one after
another via start_week). Each course's chapters carry the week (within the
course) they are studied in; a week holds one or two chapters and every chapter
is sized to fit inside a single week. Each chapter has its own deliverable;
a shared week deliverable is split on ';' across that week's chapters.

Every primary key is assigned incrementally from 1 per model, and every
foreign key / many-to-many reference is resolved by the helpers, so the fixture
is internally consistent by construction.

Run:  python make_initial.py        -> writes fixtures/initial_v16.json
"""
import json

MODEL_ORDER = [
    "curriculum.tag",
    "library.resource",
    "curriculum.course",
    "curriculum.chapter",
    "curriculum.topic",
    "roadmaps.roadmap",
    "roadmaps.roadmapcourse",
]
OUTPUT = "fixtures/initial_v16.json"

MIN_WEEK_HOURS, MAX_WEEK_HOURS = 6, 15

objs = []
counters = {}


def add(model, fields):
    counters[model] = counters.get(model, 0) + 1
    objs.append({"model": model, "pk": counters[model], "fields": fields})
    return counters[model]


_tags, _links = {}, {}


def tag(name):
    if name not in _tags:
        _tags[name] = add("curriculum.tag", {"name": name})
    return _tags[name]


def link(url):
    """The URL-only Resource for a topic link (created once per URL, on first use).

    Title, kind and author come from LINK_INFO, so every linked URL must be listed there.
    """
    if url not in _links:
        assert url in LINK_INFO, f"add {url} to LINK_INFO"
        title, kind, author = LINK_INFO[url]
        _links[url] = resource(title, author, url=url, kind=kind)
    return _links[url]


def chapter(name, description, topics):
    """topics: list of (topic_name, hours, description, [tags], [urls])"""
    # course/week/order/deliverable are filled in when course() schedules the chapter
    ch = add("curriculum.chapter", {
        "name": name, "description": description,
        "course": None, "week": None, "order": None, "deliverable": "",
        "resources": [],
    })
    hours = 0
    for order, (tname, t_hours, tdesc, ttags, turls) in enumerate(topics, 1):
        add("curriculum.topic", {
            "topic_name": tname,
            "total_time": t_hours,
            "order": order,
            "chapter": ch,
            "description": tdesc,
            "resources": [link(u) for u in turls],
            "tags": [tag(t) for t in ttags],
        })
        hours += t_hours
    assert hours <= MAX_WEEK_HOURS, f"chapter '{name}' is {hours} h, too big for one week"
    return (ch, hours)


RESOURCE_KINDS = {"book", "paper", "problem_set", "solutions", "notes", "code", "slides", "video", "other"}


def resource(title, author="", file="", url="", kind="book"):
    """Any study material: an uploaded file path (under media/), a URL, or both."""
    assert kind in RESOURCE_KINDS, kind
    assert file or url, f"resource '{title}' needs a file or a url"
    return add("library.resource", {
        "title": title, "author": author, "kind": kind,
        "file": file, "url": url, "thumbnail": None,
    })


def split_deliverable(text, parts):
    """One deliverable per chapter: a shared week deliverable splits on ';'."""
    if parts == 1:
        return [text]
    pieces = [p.strip() for p in text.split(";") if p.strip()]
    assert len(pieces) == parts, f"deliverable needs {parts} ';'-separated parts: {text}"
    return [p[0].upper() + p[1:] + ("" if p.endswith(".") else ".") for p in pieces]


def course(name, description, resources, weeks):
    """weeks: list of (title, deliverable, [chapter tuples]) -- one entry per week.

    The week title only documents the generator; the app derives a week's title
    from its chapter names. Returns (course pk, number of weeks).
    """
    co = add("curriculum.course", {"name": name, "description": description, "resources": resources})
    chapters_by_pk = {o["pk"]: o for o in objs if o["model"] == "curriculum.chapter"}
    total = 0
    for week, (title, deliverable, chapters) in enumerate(weeks, 1):
        hours = sum(h for _, h in chapters)
        assert MIN_WEEK_HOURS <= hours <= MAX_WEEK_HOURS, f"{name} week {week} '{title}' = {hours} h"
        total += hours
        for order, ((ch, _), text) in enumerate(
            zip(chapters, split_deliverable(deliverable, len(chapters))), 1
        ):
            fields = chapters_by_pk[ch]["fields"]
            assert fields["course"] is None, f"chapter {fields['name']} scheduled twice"
            fields.update(course=co, week=week, order=order, deliverable=text)
    print(f"{name}: {len(weeks)} weeks, {total} h, {total / len(weeks):.1f} h/week")
    return co, len(weeks)


def roadmap(name, description, courses):
    """courses: (course pk, weeks) in order; each starts when the previous ends."""
    rm = add("roadmaps.roadmap", {"name": name, "description": description})
    start = 1
    for order, (co, weeks) in enumerate(courses, 1):
        add("roadmaps.roadmapcourse", {
            "roadmap": rm, "course": co, "order": order, "start_week": start,
        })
        start += weeks
    print(f"{name}: {len(courses)} courses, {start - 1} weeks")
    return rm


# ---------------------------------------------------------------- tags
P, S, ML, TS, FML = "probability", "statistics", "machine-learning", "time-series", "financial-ml"
LA, IV, CODE, FIN, PROJ = "linear-algebra", "interview", "coding", "finance", "project"
PY, TH, PR, BAY, REG = "python", "theory", "practice", "bayesian", "regression"
BT, VOL, SIM, DL, CV = "backtesting", "volatility", "simulation", "deep-learning", "cross-validation"

# ---------------------------------------------------------------- links
PROBBOOK = "http://probabilitybook.net"
STAT110 = "https://stat110.hsites.harvard.edu/"
EDX110 = "https://www.edx.org/course/introduction-to-probability-0"
MIT_PROB = "https://ocw.mit.edu/courses/res-6-012-introduction-to-probability-spring-2018/"
WASSERMAN = "https://www.stat.cmu.edu/~larry/all-of-statistics/"
MIT18650 = "https://ocw.mit.edu/courses/18-650-statistics-for-applications-fall-2016/"
ISL = "https://www.statlearning.com"
ISLP_LABS = "https://github.com/intro-stat-learning/ISLP_labs"
ESL = "https://hastie.su.domains/ElemStatLearn/"
FPP3 = "https://otexts.com/fpp3/"
MIT18S096 = "https://ocw.mit.edu/courses/18-s096-topics-in-mathematics-with-applications-in-finance-fall-2013/"
STATSMODELS = "https://www.statsmodels.org/stable/"
ARCH = "https://arch.readthedocs.io/en/latest/"
QUANTRESEARCH = "https://www.quantresearch.org/"
MLFINLAB = "https://github.com/hudson-and-thames/mlfinlab"
SSRN_10REASONS = "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3104816"
SSRN_DSR = "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551"
SSRN_PBO = "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253"
MIT1806 = "https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/"
STRANG = "https://math.mit.edu/~gs/linearalgebra/"
B1B = "https://www.3blue1brown.com/topics/linear-algebra"
LEETCODE = "https://leetcode.com/"
NUMPY = "https://numpy.org/doc/stable/"
PANDAS = "https://pandas.pydata.org/docs/"
SKLEARN = "https://scikit-learn.org/stable/"
SCIPY = "https://docs.scipy.org/doc/scipy/reference/stats.html"
PYTORCH = "https://pytorch.org/"
XGBOOST = "https://xgboost.readthedocs.io/en/stable/"
YFINANCE = "https://github.com/ranaroussi/yfinance"
KAGGLE = "https://www.kaggle.com/"
INVESTOPEDIA = "https://www.investopedia.com/"

# url -> (title, kind, author) for every topic link (kept in sync with
# curriculum/migrations/0012_topic_links_to_resources.py)
LINK_INFO = {
    "http://probabilitybook.net": ("Introduction to Probability (book website)", "book", "Joseph K. Blitzstein, Jessica Hwang"),
    "https://stat110.hsites.harvard.edu/": ("Harvard Stat 110: Probability", "video", "Joseph K. Blitzstein"),
    "https://ocw.mit.edu/courses/res-6-012-introduction-to-probability-spring-2018/": ("MIT RES.6-012 Introduction to Probability", "video", "John Tsitsiklis, Patrick Jaillet"),
    "https://docs.scipy.org/doc/scipy/reference/stats.html": ("SciPy stats reference", "other", ""),
    "https://github.com/ranaroussi/yfinance": ("yfinance", "code", ""),
    "https://numpy.org/doc/stable/": ("NumPy documentation", "other", ""),
    "https://www.edx.org/course/introduction-to-probability-0": ("edX: Introduction to Probability (Stat 110)", "video", "Joseph K. Blitzstein"),
    "https://www.stat.cmu.edu/~larry/all-of-statistics/": ("All of Statistics (book website)", "book", "Larry Wasserman"),
    "https://ocw.mit.edu/courses/18-650-statistics-for-applications-fall-2016/": ("MIT 18.650 Statistics for Applications", "video", "Philippe Rigollet"),
    "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551": ("The Deflated Sharpe Ratio", "paper", "David H. Bailey, Marcos López de Prado"),
    "https://hastie.su.domains/ElemStatLearn/": ("The Elements of Statistical Learning (book website)", "book", "Trevor Hastie, Robert Tibshirani, Jerome Friedman"),
    "https://www.statsmodels.org/stable/": ("statsmodels documentation", "other", ""),
    "https://www.statlearning.com": ("An Introduction to Statistical Learning (book website)", "book", "Gareth James, Daniela Witten, Trevor Hastie, Robert Tibshirani, Jonathan Taylor"),
    "https://github.com/intro-stat-learning/ISLP_labs": ("ISLP labs", "code", ""),
    "https://pandas.pydata.org/docs/": ("pandas documentation", "other", ""),
    "https://scikit-learn.org/stable/": ("scikit-learn documentation", "other", ""),
    "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3104816": ("The 10 Reasons Most Machine Learning Funds Fail", "paper", "Marcos López de Prado"),
    "https://xgboost.readthedocs.io/en/stable/": ("XGBoost documentation", "other", ""),
    "https://pytorch.org/": ("PyTorch", "other", ""),
    "https://www.kaggle.com/": ("Kaggle", "other", ""),
    "https://ocw.mit.edu/courses/18-s096-topics-in-mathematics-with-applications-in-finance-fall-2013/": ("MIT 18.S096 Topics in Mathematics with Applications in Finance", "video", ""),
    "https://otexts.com/fpp3/": ("Forecasting: Principles and Practice, 3rd Edition (online)", "book", "Rob J. Hyndman, George Athanasopoulos"),
    "https://arch.readthedocs.io/en/latest/": ("arch documentation", "other", ""),
    "https://www.quantresearch.org/": ("QuantResearch.org", "paper", "Marcos López de Prado"),
    "https://github.com/hudson-and-thames/mlfinlab": ("mlfinlab", "code", ""),
    "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253": ("The Probability of Backtest Overfitting", "paper", "David H. Bailey, Jonathan Borwein, Marcos López de Prado, Qiji Jim Zhu"),
    "https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/": ("MIT 18.06 Linear Algebra", "video", "Gilbert Strang"),
    "https://math.mit.edu/~gs/linearalgebra/": ("Introduction to Linear Algebra (book website)", "book", "Gilbert Strang"),
    "https://www.3blue1brown.com/topics/linear-algebra": ("3Blue1Brown: Essence of Linear Algebra", "video", "Grant Sanderson"),
    "https://leetcode.com/": ("LeetCode", "problem_set", ""),
    "https://www.investopedia.com/": ("Investopedia", "other", ""),
}


# ---------------------------------------------------------------- resources
B_BLITZ = resource("Introduction to Probability, 2nd Edition",
               "Joseph K. Blitzstein, Jessica Hwang",
               file="books/blitzstein_hwang_introduction_to_probability_2e.pdf")
B_WASS = resource("All of Statistics: A Concise Course in Statistical Inference",
              "Larry Wasserman",
              file="books/wasserman_all_of_statistics.pdf")
B_ISLP = resource("An Introduction to Statistical Learning with Applications in Python",
              "Gareth James, Daniela Witten, Trevor Hastie, Robert Tibshirani, Jonathan Taylor",
              file="books/ISLP_website.pdf")
B_TSAY = resource("Analysis of Financial Time Series, 3rd Edition",
              "Ruey S. Tsay",
              file="books/tsay_analysis_of_financial_time_series_3e.pdf")
B_AFML = resource("Advances in Financial Machine Learning",
              "Marcos López de Prado",
              file="books/lopez_de_prado_advances_in_financial_machine_learning.pdf")
B_FPP3 = resource("Forecasting: Principles and Practice, 3rd Edition",
              "Rob J. Hyndman, George Athanasopoulos",
              file="books/hyndman_athanasopoulos_fpp3.pdf")
B_ZHOU = resource("A Practical Guide to Quantitative Finance Interviews",
              "Xinfeng Zhou",
              file="books/zhou_practical_guide_to_quantitative_finance_interviews.pdf",
              kind="problem_set")
B_STRANG = resource("Introduction to Linear Algebra, 5th Edition",
                "Gilbert Strang",
                file="books/strang_introduction_to_linear_algebra_5e.pdf")

# ================================================================ ROADMAP 1
# Probability with Blitzstein & Hwang -- one chapter per week
c1 = chapter("Probability and Counting",
    "Blitzstein & Hwang ch. 1. Sample spaces, the naive definition of probability, counting rules and the axioms.", [
    ("Sample spaces and the naive definition of probability", 2,
     "Define experiments, sample spaces and events; compute probabilities by counting equally likely outcomes.",
     [P, TH], [PROBBOOK, STAT110]),
    ("Counting: multiplication rule, permutations and binomial coefficients", 3,
     "The counting tools behind most discrete probability problems, including sampling with and without replacement.",
     [P, TH], [PROBBOOK]),
    ("Story proofs and the axioms of probability", 2,
     "Prove combinatorial identities by interpretation; learn the axioms and inclusion-exclusion.",
     [P, TH], [PROBBOOK, MIT_PROB]),
    ("Chapter 1 problem set", 3,
     "Work at least 20 exercises, including the birthday problem and de Montmort's matching problem.",
     [P, PR], [STAT110]),
])
c2 = chapter("Conditional Probability",
    "Blitzstein & Hwang ch. 2. Conditioning, Bayes' rule, independence and conditioning as a problem-solving tool.", [
    ("Conditional probability and Bayes' rule", 3,
     "Definition of conditioning, Bayes' rule, prior and posterior odds, the base-rate fallacy.",
     [P, TH, BAY], [PROBBOOK, STAT110]),
    ("Law of total probability and independence", 2,
     "Partition the sample space to compute probabilities; independence versus conditional independence; Simpson's paradox.",
     [P, TH], [PROBBOOK]),
    ("Conditioning as a tool: first-step analysis and gambler's ruin", 3,
     "Solve recursive problems by conditioning on the first step; the gambler's ruin problem and its finance interpretation.",
     [P, TH, FIN], [PROBBOOK, MIT_PROB]),
    ("Chapter 2 problem set", 3,
     "Exercises on Bayes' rule, the Monty Hall problem and conditional independence.",
     [P, PR], [STAT110]),
])
c3 = chapter("Random Variables and Their Distributions",
    "Blitzstein & Hwang ch. 3. Random variables as functions, PMFs, CDFs and the first named discrete distributions.", [
    ("Random variables, PMFs and CDFs", 2,
     "Random variables as maps from the sample space; probability mass functions and cumulative distribution functions.",
     [P, TH], [PROBBOOK, STAT110]),
    ("Bernoulli, binomial, hypergeometric and discrete uniform", 3,
     "Stories behind the core discrete distributions and when each applies.",
     [P, TH], [PROBBOOK]),
    ("Functions of random variables and independence", 2,
     "Distributions of transformed random variables; independence and i.i.d. samples.",
     [P, TH], [PROBBOOK]),
    ("Chapter 3 problem set", 3,
     "Exercises on identifying distributions from stories and computing PMFs.",
     [P, PR], [STAT110]),
])
c4 = chapter("Expectation",
    "Blitzstein & Hwang ch. 4. Expectation, linearity, indicator random variables, variance and the Poisson distribution.", [
    ("Expectation and linearity", 2,
     "Definition of expected value and the power of linearity for sums of dependent random variables.",
     [P, TH], [PROBBOOK, STAT110]),
    ("Geometric, negative binomial and indicator random variables", 3,
     "Waiting-time distributions and the indicator trick for counting problems.",
     [P, TH], [PROBBOOK]),
    ("LOTUS, variance and the Poisson distribution", 3,
     "Law of the unconscious statistician, variance and standard deviation, Poisson as a limit of binomials.",
     [P, TH], [PROBBOOK, MIT_PROB]),
    ("Chapter 4 problem set", 3,
     "Exercises using indicators and linearity, including the coupon collector and St. Petersburg problems.",
     [P, PR], [STAT110]),
])
c5 = chapter("Continuous Random Variables",
    "Blitzstein & Hwang ch. 5. Densities, the uniform, normal and exponential distributions, and the Poisson process.", [
    ("PDFs, CDFs and the uniform distribution", 3,
     "Probability density functions, universality of the uniform and how to generate random variables from it.",
     [P, TH, SIM], [PROBBOOK, STAT110]),
    ("The normal distribution", 3,
     "Standard normal, location-scale transformations, the 68-95-99.7 rule and why normality appears everywhere.",
     [P, TH], [PROBBOOK]),
    ("Exponential distribution and the Poisson process", 2,
     "Memorylessness, rates, and inter-arrival times; first look at the Poisson process.",
     [P, TH], [PROBBOOK, MIT_PROB]),
    ("Chapter 5 problem set", 3,
     "Exercises on densities, transformations and memorylessness.",
     [P, PR], [STAT110]),
])
c6 = chapter("Moments",
    "Blitzstein & Hwang ch. 6. Moments, skewness, kurtosis, moment generating functions and heavy-tailed returns.", [
    ("Moments, skewness and kurtosis", 3,
     "Higher moments, what skewness and kurtosis measure, and why financial returns are fat-tailed.",
     [P, TH, FIN], [PROBBOOK]),
    ("Moment generating functions", 2,
     "MGFs, sums of independent random variables and the MGF of the normal distribution.",
     [P, TH], [PROBBOOK, STAT110]),
    ("Python: sample moments of real return series", 2,
     "Download daily prices, compute returns, and estimate skewness and kurtosis with SciPy; compare with a normal fit.",
     [P, PY, FIN, PR], [SCIPY, YFINANCE]),
    ("Chapter 6 problem set", 2,
     "Exercises on moments and MGFs.",
     [P, PR], [STAT110]),
])
c7 = chapter("Joint Distributions",
    "Blitzstein & Hwang ch. 7. Joint, marginal and conditional distributions, covariance, correlation and the multivariate normal.", [
    ("Joint, marginal and conditional distributions", 3,
     "Two-dimensional PMFs and PDFs, marginalization and conditioning in the discrete and continuous cases.",
     [P, TH], [PROBBOOK, STAT110]),
    ("Covariance and correlation", 2,
     "Definitions, properties, variance of sums, and correlation as a measure of linear dependence only.",
     [P, TH, FIN], [PROBBOOK]),
    ("Multinomial and multivariate normal distributions", 3,
     "Covariance matrices, linear combinations of jointly normal variables and the multivariate normal density.",
     [P, TH, LA], [PROBBOOK, MIT_PROB]),
    ("Chapter 7 problem set", 3,
     "Exercises on joint densities, covariance and the bivariate normal.",
     [P, PR], [STAT110]),
])
c8 = chapter("Transformations",
    "Blitzstein & Hwang ch. 8. Change of variables, convolutions, Beta and Gamma distributions, and order statistics.", [
    ("Change of variables and convolutions", 3,
     "The Jacobian method for transformations and the distribution of sums of independent random variables.",
     [P, TH], [PROBBOOK, STAT110]),
    ("Beta and Gamma distributions", 3,
     "Stories and conjugacy relationships; Beta-Binomial and Gamma-Poisson.",
     [P, TH, BAY], [PROBBOOK]),
    ("Order statistics", 2,
     "Distributions of the minimum, maximum and j-th order statistic.",
     [P, TH], [PROBBOOK]),
    ("Chapter 8 problem set", 2,
     "Exercises on transformations and order statistics.",
     [P, PR], [STAT110]),
])
c9 = chapter("Conditional Expectation",
    "Blitzstein & Hwang ch. 9. Conditional expectation given an event or a random variable, Adam's and Eve's laws, and prediction.", [
    ("Conditional expectation given an event and given a random variable", 3,
     "Conditional expectation as a random variable; taking out what is known.",
     [P, TH], [PROBBOOK, STAT110]),
    ("Adam's law and Eve's law", 3,
     "Law of total expectation and law of total variance, with applications to mixtures and compound sums.",
     [P, TH], [PROBBOOK, MIT_PROB]),
    ("Conditional expectation as prediction", 2,
     "Conditional expectation as the best predictor in mean squared error; the link to regression.",
     [P, TH, REG], [PROBBOOK]),
    ("Chapter 9 problem set", 3,
     "Exercises on Adam's and Eve's laws and prediction problems.",
     [P, PR], [STAT110]),
])
c10 = chapter("Inequalities and Limit Theorems",
    "Blitzstein & Hwang ch. 10. Markov, Chebyshev, Jensen and Cauchy-Schwarz inequalities; the law of large numbers and the central limit theorem.", [
    ("Markov, Chebyshev, Jensen and Cauchy-Schwarz", 2,
     "The core inequalities and how they bound tail probabilities and expectations.",
     [P, TH], [PROBBOOK, STAT110]),
    ("Law of large numbers and central limit theorem", 3,
     "Statements, intuition and sketch proofs; what the CLT does and does not say about heavy tails.",
     [P, TH], [PROBBOOK, MIT_PROB]),
    ("Python: simulate the CLT and chi-square and t distributions", 2,
     "Simulate sample means from several distributions, check convergence to normal, and see where the t distribution comes from.",
     [P, PY, SIM, PR], [SCIPY, NUMPY]),
    ("Chapter 10 problem set", 2,
     "Exercises on inequalities and limit theorems.",
     [P, PR], [STAT110]),
])
c11 = chapter("Markov Chains",
    "Blitzstein & Hwang ch. 11. The Markov property, transition matrices, stationary distributions and reversibility.", [
    ("Markov property and transition matrices", 2,
     "Define Markov chains, n-step transition probabilities and matrix powers.",
     [P, TH, LA], [PROBBOOK, STAT110]),
    ("Classification of states and stationary distributions", 3,
     "Recurrent and transient states, irreducibility, periodicity, existence and uniqueness of the stationary distribution.",
     [P, TH, LA], [PROBBOOK, MIT_PROB]),
    ("Reversibility and random walks on graphs", 2,
     "Detailed balance, reversible chains and random walks, with a preview of MCMC.",
     [P, TH], [PROBBOOK]),
    ("Chapter 11 problem set", 2,
     "Exercises on stationary distributions and absorbing chains.",
     [P, PR], [STAT110]),
])
c12 = chapter("Probability Review and Consolidation",
    "Mixed review across all chapters plus a small simulation project to confirm the material is usable, not just read.", [
    ("Mixed review problems", 4,
     "Solve 30 problems chosen across chapters 1-11 without looking up which chapter they came from.",
     [P, PR, IV], [STAT110, EDX110]),
    ("Python simulation mini-project", 4,
     "Pick three results (e.g. gambler's ruin, coupon collector, a Markov chain stationary distribution) and verify them by Monte Carlo.",
     [P, PY, SIM, PROJ], [NUMPY, SCIPY]),
    ("Self-assessment", 2,
     "Attempt a timed set of 10 interview-style probability questions and record which topics need revisiting.",
     [P, IV, PR], [STAT110]),
])

COURSE_1 = course(
    "Probability with Blitzstein & Hwang",
    "Chapters 1-11 of Introduction to Probability, one chapter per week, with Harvard Stat 110 lectures and problem sets. "
    "Builds the probability foundation that every later roadmap assumes, up to and including Markov chains.",
    [B_BLITZ], [
    ("Probability and counting",
     "Chapter 1 problem set with written solutions to at least 20 exercises.", [c1]),
    ("Conditional probability",
     "Chapter 2 problem set; a half-page explanation of Bayes' rule with a worked base-rate example.", [c2]),
    ("Random variables and their distributions",
     "Chapter 3 problem set; a one-page cheat sheet of named discrete distributions with their stories.", [c3]),
    ("Expectation",
     "Chapter 4 problem set, including the coupon-collector problem solved with indicators.", [c4]),
    ("Continuous random variables",
     "Chapter 5 problem set; a short script generating normal and exponential samples from uniforms.", [c5]),
    ("Moments",
     "Chapter 6 problem set; a notebook computing sample moments of real return series against a normal fit.", [c6]),
    ("Joint distributions",
     "Chapter 7 problem set; a one-page summary of covariance rules and the multivariate normal.", [c7]),
    ("Transformations",
     "Chapter 8 problem set; a derivation of the distribution of the maximum of n uniforms.", [c8]),
    ("Conditional expectation",
     "Chapter 9 problem set; a worked example of Eve's law on a compound-sum problem.", [c9]),
    ("Inequalities and limit theorems",
     "Chapter 10 problem set; a notebook that simulates the CLT from three different distributions.", [c10]),
    ("Markov chains",
     "Chapter 11 problem set; a notebook that computes and simulates a stationary distribution.", [c11]),
    ("Review and consolidation",
     "30 mixed review problems, the Monte Carlo mini-project notebook, and a self-assessment with weak areas listed.", [c12]),
])

# ================================================================ ROADMAP 2
# Statistical Inference with Wasserman -- one chapter per week
w5 = chapter("Convergence of Random Variables",
    "Wasserman ch. 5. Modes of convergence, the law of large numbers and CLT with proofs, and the delta method.", [
    ("Types of convergence", 3,
     "Convergence in probability, in distribution and in quadratic mean, and the relationships between them.",
     [S, TH], [WASSERMAN]),
    ("Law of large numbers and CLT revisited", 2,
     "Proofs via Chebyshev and characteristic functions; the Berry-Esseen bound on CLT accuracy.",
     [S, TH], [WASSERMAN, MIT18650]),
    ("The delta method", 2,
     "Asymptotic distributions of smooth functions of estimators; application to the Sharpe ratio.",
     [S, TH, FIN], [WASSERMAN]),
    ("Chapter 5 exercises", 3,
     "Selected exercises on convergence and the delta method.",
     [S, PR], [WASSERMAN]),
])
w6 = chapter("Models, Statistical Inference and Learning",
    "Wasserman ch. 6. Parametric and nonparametric models, point estimation, confidence sets and the vocabulary of inference.", [
    ("Parametric versus nonparametric models", 2,
     "What a statistical model is, identifiability, and the trade-off between assumptions and flexibility.",
     [S, TH], [WASSERMAN]),
    ("Point estimation: bias, standard error, MSE and consistency", 3,
     "The properties used to judge an estimator and the bias-variance decomposition of mean squared error.",
     [S, TH], [WASSERMAN, MIT18650]),
    ("Confidence sets and hypothesis testing overview", 2,
     "The meaning of a confidence interval and of a test, before the detailed treatment in later chapters.",
     [S, TH], [WASSERMAN]),
    ("Chapter 6 exercises", 2,
     "Exercises on bias and MSE of simple estimators.",
     [S, PR], [WASSERMAN]),
])
w7 = chapter("Estimating the CDF and Statistical Functionals",
    "Wasserman ch. 7. The empirical distribution function, plug-in estimators and statistical functionals.", [
    ("Empirical distribution function and the DKW inequality", 2,
     "Properties of the empirical CDF, Glivenko-Cantelli and a confidence band from the DKW inequality.",
     [S, TH], [WASSERMAN]),
    ("Plug-in estimators and statistical functionals", 2,
     "Estimate means, quantiles, correlations and other functionals by plugging in the empirical CDF.",
     [S, TH], [WASSERMAN]),
    ("Influence functions", 2,
     "Standard errors for plug-in estimators via the influence function; robustness intuition.",
     [S, TH], [WASSERMAN]),
    ("Chapter 7 exercises", 2,
     "Exercises on the empirical CDF and plug-in estimation.",
     [S, PR], [WASSERMAN]),
])
w8 = chapter("The Bootstrap",
    "Wasserman ch. 8. Bootstrap variance estimation and confidence intervals, with a finance application.", [
    ("Bootstrap variance estimation", 2,
     "The resampling idea, simulation versus bootstrap, and when the bootstrap fails.",
     [S, TH, SIM], [WASSERMAN]),
    ("Bootstrap confidence intervals", 3,
     "Normal, pivotal and percentile intervals and how they compare.",
     [S, TH], [WASSERMAN, MIT18650]),
    ("Python: bootstrap the Sharpe ratio of a return series", 3,
     "Compute a Sharpe ratio, bootstrap its distribution, and compare the interval with the delta-method answer; try a block bootstrap.",
     [S, PY, FIN, PR], [NUMPY, SCIPY, YFINANCE]),
    ("Chapter 8 exercises", 2,
     "Exercises on bootstrap intervals.",
     [S, PR], [WASSERMAN]),
])
w9a = chapter("Method of Moments and Maximum Likelihood",
    "Wasserman ch. 9, first half. Method of moments and the properties of maximum likelihood estimators.", [
    ("Method of moments", 2,
     "Match sample and population moments; consistency and asymptotic normality.",
     [S, TH], [WASSERMAN]),
    ("Maximum likelihood: consistency, equivariance and asymptotic normality", 4,
     "Derive MLEs, understand why they are consistent and asymptotically normal, and compute their standard errors.",
     [S, TH], [WASSERMAN, MIT18650]),
    ("MLE derivation exercises", 3,
     "Derive MLEs for the Bernoulli, Poisson, exponential, normal and uniform models and check them numerically.",
     [S, PR], [WASSERMAN]),
])
w9b = chapter("Fisher Information and the Cramér-Rao Bound",
    "Wasserman ch. 9, second half. Fisher information, efficiency, multiparameter models and the parametric bootstrap.", [
    ("Fisher information and the Cramér-Rao bound", 3,
     "Information as curvature of the log-likelihood; the lower bound on estimator variance and efficiency.",
     [S, TH], [WASSERMAN]),
    ("Multiparameter models and the parametric bootstrap", 2,
     "Fisher information matrices, the multiparameter delta method and bootstrapping under a parametric model.",
     [S, TH, LA], [WASSERMAN]),
    ("Python: MLE standard errors from Fisher information versus bootstrap", 2,
     "Fit a Student-t to returns by maximum likelihood with SciPy and compare information-based and bootstrap standard errors.",
     [S, PY, FIN, PR], [SCIPY, YFINANCE]),
    ("Chapter 9 exercises on information and efficiency", 2,
     "Exercises on Fisher information and the Cramér-Rao bound.",
     [S, PR], [WASSERMAN]),
])
w10a = chapter("Hypothesis Testing and p-values",
    "Wasserman ch. 10, first half. The Neyman-Pearson framework, Wald, likelihood ratio and chi-square tests, and p-values.", [
    ("Neyman-Pearson framework, power and error types", 3,
     "Null and alternative, Type I and II errors, size and power, and how to design a test.",
     [S, TH], [WASSERMAN, MIT18650]),
    ("Wald, likelihood ratio and chi-square tests", 3,
     "Construct and interpret the standard large-sample tests; goodness of fit.",
     [S, TH], [WASSERMAN]),
    ("p-values: what they mean and do not mean", 2,
     "Definition, distribution under the null, and common misinterpretations.",
     [S, TH], [WASSERMAN]),
    ("Test construction exercises", 2,
     "Exercises on building tests, computing power and interpreting p-values.",
     [S, PR], [WASSERMAN]),
])
w10b = chapter("Multiple Testing",
    "Wasserman ch. 10, second half. Family-wise error rate, false discovery rate, and why this is the central statistical problem in strategy research.", [
    ("Family-wise error rate: Bonferroni and Holm", 2,
     "How many tests inflate false positives and the corrections that control the family-wise error rate.",
     [S, TH], [WASSERMAN]),
    ("False discovery rate and Benjamini-Hochberg", 3,
     "FDR versus FWER, the BH procedure, and when controlling FDR is the right choice.",
     [S, TH, FIN, BT], [WASSERMAN, SSRN_DSR]),
    ("Python: run many tests on random signals", 3,
     "Test hundreds of random 'signals' against returns, then apply Bonferroni and BH and count what survives.",
     [S, PY, BT, PR], [SCIPY, NUMPY]),
    ("Multiple-testing exercises", 2,
     "Exercises on FWER and FDR control.",
     [S, PR], [WASSERMAN]),
])
w11 = chapter("Bayesian Inference",
    "Wasserman ch. 11. Priors, posteriors, conjugacy, Bayesian intervals and the Bayesian view of regularization.", [
    ("Priors, posteriors and conjugacy", 3,
     "Bayes' theorem for parameters; Beta-Binomial and Normal-Normal conjugate updates.",
     [S, TH, BAY], [WASSERMAN]),
    ("Bayesian point and interval estimation; large-sample behavior", 2,
     "Posterior mean and MAP estimates, credible intervals and the Bernstein-von Mises connection to MLE.",
     [S, TH, BAY], [WASSERMAN, MIT18650]),
    ("Shrinkage and the Bayesian view of regularization", 2,
     "How Gaussian and Laplace priors give ridge and lasso; shrinkage estimators for noisy means and covariances.",
     [S, TH, BAY, REG], [WASSERMAN, ESL]),
    ("Chapter 11 exercises", 2,
     "Exercises on conjugate updating and posterior intervals.",
     [S, PR, BAY], [WASSERMAN]),
])
w12 = chapter("Statistical Decision Theory",
    "Wasserman ch. 12. Loss and risk, Bayes and minimax estimators, admissibility and James-Stein shrinkage.", [
    ("Loss, risk, Bayes and minimax estimators", 3,
     "Compare estimators by their risk functions; Bayes risk and minimax criteria.",
     [S, TH, BAY], [WASSERMAN]),
    ("Admissibility and James-Stein shrinkage", 3,
     "Why the sample mean is inadmissible in three or more dimensions, and what that implies for estimating many expected returns.",
     [S, TH, FIN], [WASSERMAN, ESL]),
    ("Chapter 12 exercises", 2,
     "Exercises on risk functions and shrinkage.",
     [S, PR], [WASSERMAN]),
])
w13 = chapter("Linear and Logistic Regression",
    "Wasserman ch. 13. Least squares in matrix form, inference for coefficients, model selection and logistic regression.", [
    ("Simple and multiple regression in matrix form", 4,
     "Least squares as projection, the hat matrix, Gauss-Markov and the sampling distribution of coefficients.",
     [S, TH, REG, LA], [WASSERMAN, MIT18650]),
    ("Inference for coefficients and model selection", 3,
     "Standard errors, t-tests, confidence intervals, Mallows' Cp, AIC, BIC and cross-validation.",
     [S, TH, REG, CV], [WASSERMAN]),
    ("Logistic regression", 2,
     "The logistic model, maximum likelihood fitting and interpretation of coefficients.",
     [S, TH, REG], [WASSERMAN]),
    ("Chapter 13 exercises", 3,
     "Exercises on least squares derivations and regression inference.",
     [S, PR, REG], [WASSERMAN]),
])
w14 = chapter("Regression Diagnostics and Hypothesis-Testing Project",
    "Apply the inference toolkit: regression diagnostics on real returns and a small project that tests a trading hypothesis properly.", [
    ("Python: regression diagnostics with statsmodels", 3,
     "Fit a factor regression on stock returns, check residuals, heteroscedasticity and collinearity, and use robust standard errors.",
     [S, PY, REG, FIN, PR], [STATSMODELS, YFINANCE]),
    ("Mini-project: test a calendar or momentum effect with multiple-testing correction", 6,
     "Test several candidate effects on historical returns, report raw and FDR-adjusted p-values, and bootstrap the effect sizes.",
     [S, PY, FIN, PROJ, BT], [YFINANCE, STATSMODELS, SCIPY]),
    ("Mixed review and self-assessment", 3,
     "Solve 15 problems across chapters 5-13, then a timed set of 10 interview-style statistics questions; list weak areas.",
     [S, IV, PR], [WASSERMAN, MIT18650]),
])

COURSE_2 = course(
    "Statistical Inference with Wasserman",
    "Chapters 5-13 of All of Statistics, one chapter (or half-chapter) per week: convergence, estimation, bootstrap, "
    "maximum likelihood, testing, multiple testing, Bayesian inference, decision theory and regression. "
    "The theory that quant research and interviews assume.",
    [B_WASS], [
    ("Convergence of random variables",
     "Chapter 5 exercises; a derivation of the asymptotic variance of the Sharpe ratio by the delta method.", [w5]),
    ("Models and the language of inference",
     "Chapter 6 exercises; a one-page summary of estimator properties (bias, SE, MSE, consistency).", [w6]),
    ("Empirical CDF and statistical functionals",
     "Chapter 7 exercises; a plot of an empirical CDF with its DKW confidence band.", [w7]),
    ("The bootstrap",
     "Chapter 8 exercises; a notebook bootstrapping the Sharpe ratio with ordinary and block bootstrap.", [w8]),
    ("Method of moments and maximum likelihood",
     "Written MLE derivations and asymptotic variances for at least five distributions.", [w9a]),
    ("Fisher information and the Cramér-Rao bound",
     "Chapter 9 exercises; a notebook comparing information-based and bootstrap standard errors for a Student-t fit.", [w9b]),
    ("Hypothesis testing and p-values",
     "Test-construction exercises; a half-page on what a p-value is and is not.", [w10a]),
    ("Multiple testing",
     "A notebook running hundreds of tests on random signals with Bonferroni and BH corrections, plus a written FWER-versus-FDR explanation.", [w10b]),
    ("Bayesian inference",
     "Chapter 11 exercises; a worked Normal-Normal update and a note on how priors give ridge and lasso.", [w11]),
    ("Statistical decision theory",
     "Chapter 12 exercises; a short simulation showing James-Stein beating the sample mean.", [w12]),
    ("Linear and logistic regression",
     "Chapter 13 exercises; a derivation of the OLS estimator and its covariance in matrix form.", [w13]),
    ("Regression diagnostics and testing project",
     "The regression-diagnostics notebook; the multiple-testing mini-project write-up; self-assessment with weak areas listed.", [w14]),
])

# ================================================================ ROADMAP 3
# Machine Learning with ISLP -- one chapter per week
i2 = chapter("Statistical Learning",
    "ISLP ch. 2. What statistical learning is, the bias-variance trade-off and how to assess model accuracy.", [
    ("Prediction versus inference; parametric and nonparametric methods", 2,
     "Why we estimate f, the accuracy-interpretability trade-off and supervised versus unsupervised learning.",
     [ML, TH], [ISL]),
    ("Bias-variance trade-off and assessing model accuracy", 3,
     "Training versus test error, the bias-variance decomposition, and the Bayes classifier.",
     [ML, TH], [ISL, ESL]),
    ("Lab: Python, NumPy, pandas and the ISLP package", 3,
     "Work through the chapter 2 lab to set up the environment used by every later lab.",
     [ML, PY, PR], [ISLP_LABS, NUMPY, PANDAS]),
])
i3 = chapter("Linear Regression",
    "ISLP ch. 3. Simple and multiple linear regression, interactions, qualitative predictors and diagnostics.", [
    ("Simple and multiple linear regression", 3,
     "Estimating coefficients, assessing accuracy and the F-test for overall fit.",
     [ML, REG, TH], [ISL]),
    ("Interactions, qualitative predictors and potential problems", 3,
     "Dummy variables, interaction terms, non-linearity, correlated errors, heteroscedasticity, outliers and collinearity.",
     [ML, REG, TH], [ISL]),
    ("Lab: linear regression in Python", 3,
     "Fit, diagnose and extend regression models using statsmodels and the ISLP helpers.",
     [ML, REG, PY, PR], [ISLP_LABS, STATSMODELS]),
    ("Chapter 3 exercises", 3,
     "Conceptual and applied exercises on regression.",
     [ML, REG, PR], [ISL]),
])
i4 = chapter("Classification",
    "ISLP ch. 4. Logistic regression, discriminant analysis, naive Bayes, KNN and generalized linear models.", [
    ("Logistic regression", 2,
     "Odds, the logistic model, multinomial extension and interpretation.",
     [ML, TH, REG], [ISL]),
    ("LDA, QDA, naive Bayes and KNN", 3,
     "Generative classifiers versus discriminative ones and when each wins; ROC curves and confusion matrices.",
     [ML, TH], [ISL, ESL]),
    ("Generalized linear models", 1,
     "Poisson regression and the GLM family.",
     [ML, TH, REG], [ISL]),
    ("Lab: classification in Python", 3,
     "Fit classifiers on the Smarket data and compare them with proper held-out evaluation.",
     [ML, PY, PR, FIN], [ISLP_LABS, SKLEARN]),
])
i5 = chapter("Resampling Methods",
    "ISLP ch. 5. Cross-validation and the bootstrap, and why standard cross-validation breaks on time series.", [
    ("Cross-validation: validation set, LOOCV and k-fold", 3,
     "Estimating test error, the bias-variance trade-off of k, and cross-validation for classification.",
     [ML, CV, TH], [ISL]),
    ("The bootstrap", 2,
     "Resampling to estimate the variability of any estimator.",
     [ML, TH, SIM], [ISL]),
    ("Why random k-fold fails on financial time series", 2,
     "Leakage through autocorrelation and overlapping labels; preview of walk-forward and purged cross-validation.",
     [ML, CV, TS, FML], [SSRN_10REASONS]),
    ("Lab: cross-validation and the bootstrap", 3,
     "Implement CV and bootstrap with scikit-learn, then write a simple walk-forward splitter.",
     [ML, PY, CV, PR], [ISLP_LABS, SKLEARN]),
])
i6 = chapter("Linear Model Selection and Regularization",
    "ISLP ch. 6. Subset selection, ridge, lasso, dimension reduction and high-dimensional data.", [
    ("Subset selection and model-selection criteria", 2,
     "Best subset, forward and backward stepwise selection; Cp, AIC, BIC, adjusted R-squared.",
     [ML, REG, TH], [ISL]),
    ("Ridge and lasso", 3,
     "Shrinkage penalties, the geometry of L1 versus L2, selecting the tuning parameter by CV, and the Bayesian interpretation.",
     [ML, REG, TH, BAY], [ISL, ESL]),
    ("PCR, PLS and high-dimensional considerations", 2,
     "Dimension reduction methods and what goes wrong when p is comparable to n.",
     [ML, REG, TH, LA], [ISL]),
    ("Lab: regularization in Python", 3,
     "Fit ridge and lasso paths with scikit-learn and choose penalties with cross-validation.",
     [ML, REG, PY, PR], [ISLP_LABS, SKLEARN]),
])
i8 = chapter("Tree-Based Methods",
    "ISLP ch. 8. Decision trees, bagging, random forests, boosting and BART.", [
    ("Decision trees", 2,
     "Recursive binary splitting, pruning, and trees versus linear models.",
     [ML, TH], [ISL]),
    ("Bagging and random forests", 2,
     "Variance reduction by averaging, out-of-bag error and variable importance.",
     [ML, TH], [ISL, ESL]),
    ("Boosting and gradient boosting", 3,
     "Sequential fitting to residuals, learning rate and depth, and the gradient boosting view used by XGBoost and LightGBM.",
     [ML, TH], [ISL, XGBOOST]),
    ("Lab: random forests and boosting in Python", 3,
     "Fit forests and boosted models, tune them with CV and compare feature importances.",
     [ML, PY, PR], [ISLP_LABS, SKLEARN, XGBOOST]),
])
i10 = chapter("Deep Learning",
    "ISLP ch. 10. Neural networks, convolutional and recurrent architectures, and how networks are fitted.", [
    ("Single-layer and multilayer neural networks", 3,
     "Hidden units, activations and why depth helps.",
     [ML, DL, TH], [ISL]),
    ("CNNs and RNNs; sequence models for time series", 3,
     "Convolutional layers, recurrent networks and their use on sequential financial data.",
     [ML, DL, TS, TH], [ISL]),
    ("Fitting neural networks: SGD, backpropagation, regularization and dropout", 3,
     "How training works, the double-descent phenomenon and interpolation.",
     [ML, DL, TH], [ISL, ESL]),
    ("Lab: deep learning with PyTorch", 4,
     "Work through the chapter 10 lab, then fit a small network on a return-prediction task.",
     [ML, DL, PY, PR], [ISLP_LABS, PYTORCH]),
])
i12 = chapter("Unsupervised Learning",
    "ISLP ch. 12. Principal components, clustering and matrix completion.", [
    ("Principal components analysis", 3,
     "PCA as variance maximization and as low-rank approximation; proportion of variance explained.",
     [ML, LA, TH], [ISL, ESL]),
    ("K-means and hierarchical clustering", 2,
     "Clustering algorithms, choosing the number of clusters and the pitfalls of clustering.",
     [ML, TH], [ISL]),
    ("Matrix completion and missing values", 1,
     "Low-rank imputation and its use on incomplete data.",
     [ML, LA, TH], [ISL]),
    ("Lab: PCA and clustering in Python", 3,
     "Run PCA on a panel of stock returns and cluster assets by return correlation.",
     [ML, PY, PR, FIN], [ISLP_LABS, SKLEARN, YFINANCE]),
])
i13 = chapter("Multiple Testing",
    "ISLP ch. 13. Family-wise error rate, false discovery rate and resampling approaches, applied to strategy selection.", [
    ("Family-wise error rate", 2,
     "Why many tests inflate false positives; Bonferroni and Holm corrections.",
     [ML, S, TH], [ISL]),
    ("False discovery rate and Benjamini-Hochberg", 2,
     "Controlling FDR instead of FWER and when that is the right choice.",
     [ML, S, TH], [ISL]),
    ("Resampling approaches and application to strategy selection", 2,
     "Permutation-based p-values and the deflated Sharpe ratio as multiple-testing correction for backtests.",
     [ML, S, FIN, BT], [ISL, SSRN_DSR]),
    ("Lab: multiple testing in Python", 2,
     "Run many tests on random signals, apply Bonferroni and BH, and see how many survive.",
     [ML, PY, PR], [ISLP_LABS, SCIPY]),
])
i14 = chapter("ISLP Project: Return Prediction with Walk-Forward Validation",
    "Apply the ISLP toolkit to real market data with honest validation.", [
    ("Build a feature set from price data", 4,
     "Compute lagged returns, rolling volatility and momentum features with pandas, aligned to avoid look-ahead.",
     [ML, PY, FIN, PROJ], [PANDAS, YFINANCE]),
    ("Compare ridge, lasso, random forest and boosting with walk-forward validation", 6,
     "Evaluate each model out of sample with an expanding-window scheme and report metrics with uncertainty.",
     [ML, PY, CV, FIN, PROJ], [SKLEARN, XGBOOST]),
    ("Write-up with honest out-of-sample results", 3,
     "Document what worked, what did not, and what the results would mean after transaction costs.",
     [ML, PROJ, IV], [KAGGLE]),
])

COURSE_3 = course(
    "Machine Learning with ISLP",
    "Chapters 2-6, 8, 10, 12 and 13 of An Introduction to Statistical Learning (Python edition), one chapter per week "
    "with its lab, ending in a return-prediction project with walk-forward validation.",
    [B_ISLP], [
    ("Statistical learning",
     "Lab 2 completed; environment ready for all later labs; a written bias-variance explanation.", [i2]),
    ("Linear regression",
     "Lab 3 completed; chapter 3 exercises.", [i3]),
    ("Classification",
     "Lab 4 completed; a comparison table of logistic regression, LDA, QDA and KNN on the Smarket data.", [i4]),
    ("Resampling methods",
     "Lab 5 completed; a working walk-forward cross-validation splitter in Python.", [i5]),
    ("Model selection and regularization",
     "Lab 6 completed; a notebook with ridge and lasso paths and CV-chosen penalties.", [i6]),
    ("Tree-based methods",
     "Lab 8 completed; a notebook comparing random forest and boosting with feature importances.", [i8]),
    ("Deep learning",
     "Lab 10 completed; a small PyTorch model trained on a return-prediction task.", [i10]),
    ("Unsupervised learning",
     "Lab 12 completed; PCA and clustering notebook on a panel of stock returns.", [i12]),
    ("Multiple testing",
     "Lab 13 completed; a notebook showing how many random signals survive Bonferroni and BH.", [i13]),
    ("Return-prediction project",
     "Project notebook comparing four models under walk-forward validation, with a write-up of out-of-sample results.", [i14]),
])

# ================================================================ ROADMAP 4
# Financial Time Series with Tsay -- one chapter per week
t1 = chapter("Financial Time Series and Their Characteristics",
    "Tsay ch. 1. Asset returns, their distributional properties and the stylized facts of financial data.", [
    ("Asset returns: simple, log, multi-period and excess returns", 2,
     "Definitions and why log returns are convenient for modeling.",
     [TS, FIN, TH], [MIT18S096]),
    ("Distributional properties: fat tails, skewness and normality tests", 3,
     "Empirical moments, Jarque-Bera, QQ plots and the stylized facts: fat tails, volatility clustering, weak autocorrelation.",
     [TS, FIN, S, TH], [MIT18S096]),
    ("Python: load prices and explore return distributions", 3,
     "Download several assets, compute returns at different horizons and compare their distributions and autocorrelations.",
     [TS, PY, FIN, PR], [YFINANCE, PANDAS, SCIPY]),
])
t2a = chapter("Stationarity and ARMA Models",
    "Tsay ch. 2, first half (Hyndman ch. 2, 5 and 9 as a gentler alternative). Stationarity, autocorrelation and ARMA modeling.", [
    ("Stationarity, autocorrelation, ACF and PACF, Ljung-Box test", 3,
     "Weak stationarity, sample autocorrelations and testing for serial dependence.",
     [TS, TH], [FPP3, MIT18S096]),
    ("AR, MA and ARMA models: identification, estimation and forecasting", 4,
     "Model structure, order selection with ACF/PACF and information criteria, and multi-step forecasts.",
     [TS, TH], [FPP3]),
    ("Python: fit ARMA models with statsmodels", 3,
     "Fit, diagnose and forecast ARMA models on returns; verify that the residuals pass Ljung-Box.",
     [TS, PY, PR], [STATSMODELS]),
])
t2b = chapter("Unit Roots and Regression with Time Series",
    "Tsay ch. 2, second half. Random walks, unit-root tests, spurious regression and seasonality.", [
    ("Unit roots: random walks, differencing and the ADF test", 3,
     "Random walk with drift, trend versus difference stationarity and the augmented Dickey-Fuller test.",
     [TS, TH, FIN], [FPP3]),
    ("Regression with time series errors and seasonality", 2,
     "Spurious regression, autocorrelated residuals and seasonal models.",
     [TS, REG, TH], [FPP3]),
    ("Python: ADF tests and a spurious-regression simulation", 3,
     "Run ADF tests on prices and returns, then regress two independent random walks on each other to see the spurious t-statistic.",
     [TS, PY, SIM, PR], [STATSMODELS, NUMPY]),
])
t3 = chapter("Conditional Heteroscedastic Models",
    "Tsay ch. 3. ARCH and GARCH models for volatility clustering, asymmetric extensions and volatility forecasting.", [
    ("Volatility clustering and the ARCH effect", 2,
     "Why squared returns are autocorrelated; testing for ARCH effects.",
     [TS, VOL, TH], [MIT18S096]),
    ("GARCH, IGARCH, GARCH-M, EGARCH and asymmetric models", 4,
     "Model structure, estimation by quasi-maximum likelihood and the leverage effect.",
     [TS, VOL, TH], [ARCH]),
    ("Volatility forecasting and evaluation", 2,
     "Multi-step variance forecasts, realized volatility as a benchmark and forecast evaluation.",
     [TS, VOL, TH, FIN], [ARCH]),
    ("Python: GARCH with the arch package", 3,
     "Fit GARCH(1,1) and an asymmetric variant on index returns and compare their volatility forecasts.",
     [TS, VOL, PY, PR], [ARCH]),
])
t8 = chapter("Multivariate Time Series and Cointegration",
    "Tsay ch. 8. Vector autoregression, cointegration tests, error-correction models and pairs trading.", [
    ("Cross-correlation and vector autoregression", 3,
     "VAR models, order selection, impulse responses and Granger causality.",
     [TS, LA, TH], [STATSMODELS]),
    ("Cointegration: Engle-Granger and Johansen tests", 3,
     "Why two non-stationary series can have a stationary combination, and how to test for it.",
     [TS, TH, FIN], [MIT18S096]),
    ("Error-correction models and pairs trading", 3,
     "Vector error-correction models and the logic of mean-reversion trades on the cointegrating spread.",
     [TS, FIN, TH], [MIT18S096]),
    ("Python: pairs-trading backtest sketch", 4,
     "Find a cointegrated pair, estimate the hedge ratio, trade the z-score of the spread and evaluate with costs.",
     [TS, PY, FIN, BT, PR], [STATSMODELS, YFINANCE]),
])
t9 = chapter("Principal Component Analysis and Factor Models",
    "Tsay ch. 9. PCA of return panels, statistical factor models and factor regressions.", [
    ("Principal components of return panels", 2,
     "Eigen-decomposition of the covariance matrix, the market factor as the first component and random-matrix noise.",
     [TS, LA, TH], [MIT18S096]),
    ("Statistical and fundamental factor models", 3,
     "Factor models for returns, Fama-French style regressions and factor exposures.",
     [TS, FIN, REG, TH], [MIT18S096]),
    ("Python: PCA on a stock universe", 3,
     "Run PCA on a panel of daily returns, examine loadings and the scree plot, and compare with a market-beta regression.",
     [TS, PY, LA, PR], [NUMPY, SKLEARN, YFINANCE]),
])
t11 = chapter("State-Space Models and the Kalman Filter",
    "Tsay ch. 11. State-space representation, the Kalman filter and smoother, and time-varying parameter models.", [
    ("State-space representation: local level and local trend models", 3,
     "Observation and state equations; expressing ARMA and structural models in state-space form.",
     [TS, TH, LA], [FPP3]),
    ("Kalman filter: prediction, filtering and smoothing", 4,
     "Derive the recursions and understand the Kalman gain as a Bayesian update.",
     [TS, TH, BAY, LA], [MIT18S096]),
    ("Applications: time-varying betas and dynamic hedge ratios", 3,
     "Treat regression coefficients as states to track changing exposures.",
     [TS, FIN, REG, TH], [STATSMODELS]),
    ("Python: Kalman filter with statsmodels", 3,
     "Fit a local-level model and a time-varying beta regression using statsmodels state-space tools.",
     [TS, PY, PR], [STATSMODELS]),
])

COURSE_4 = course(
    "Financial Time Series with Tsay",
    "Chapters 1, 2, 3, 8, 9 and 11 of Analysis of Financial Time Series, one chapter (or half-chapter) per week, "
    "with Hyndman's free Forecasting: Principles and Practice as a gentler reference. "
    "Stationarity, ARMA, GARCH, cointegration, factor models and the Kalman filter.",
    [B_TSAY, B_FPP3], [
    ("Return characteristics",
     "Exploration notebook on return distributions and autocorrelations at several horizons.", [t1]),
    ("Stationarity and ARMA models",
     "ARMA fits with Ljung-Box diagnostics on at least three return series.", [t2a]),
    ("Unit roots and regression with time series",
     "ADF-test notebook plus the spurious-regression simulation with a short written interpretation.", [t2b]),
    ("Volatility models",
     "GARCH notebook with symmetric and asymmetric fits and forecast evaluation against realized volatility.", [t3]),
    ("Multivariate series and cointegration",
     "Pairs-trading backtest sketch on a cointegrated pair, with transaction costs included.", [t8]),
    ("PCA and factor models",
     "PCA notebook on a stock universe with loadings, scree plot and a market-beta comparison.", [t9]),
    ("State-space models and the Kalman filter",
     "Kalman-filter notebook with a local-level model and a time-varying beta example.", [t11]),
])

# ================================================================ ROADMAP 5
# Financial Machine Learning with López de Prado -- one or two chapters per week
a2 = chapter("Financial Data Structures",
    "AFML ch. 1-2. Why standard ML fails in finance and how to build information-driven bars.", [
    ("Why most machine learning funds fail", 2,
     "The ten pitfalls: integer differentiation, inefficient sampling, wrong labeling, non-IID weighting, leakage, overfitting.",
     [FML, TH], [SSRN_10REASONS, QUANTRESEARCH]),
    ("Bars: time, tick, volume, dollar and information-driven bars", 3,
     "Sampling by activity instead of clock time and why it improves statistical properties.",
     [FML, TS, TH], [MLFINLAB]),
    ("Python: build dollar bars from intraday data", 3,
     "Construct dollar bars from trade or minute data and compare their return distributions with time bars.",
     [FML, PY, PR], [PANDAS, MLFINLAB]),
])
a3 = chapter("Labeling",
    "AFML ch. 3. Fixed-horizon labels, the triple-barrier method and meta-labeling.", [
    ("Fixed-time horizon labeling and its problems", 1,
     "Why the usual labeling ignores volatility and the path of prices.",
     [FML, TH], [SSRN_10REASONS]),
    ("The triple-barrier method", 3,
     "Profit-taking, stop-loss and vertical barriers; volatility-scaled thresholds.",
     [FML, TH], [MLFINLAB]),
    ("Meta-labeling", 2,
     "Separate the side of a bet from its size; a secondary model that predicts whether the primary signal is right.",
     [FML, ML, TH], [QUANTRESEARCH]),
    ("Python: implement triple-barrier labels", 3,
     "Code the triple-barrier method on dollar bars and inspect label balance and duration.",
     [FML, PY, PR], [PANDAS, MLFINLAB]),
])
a4 = chapter("Sample Weights",
    "AFML ch. 4. Overlapping outcomes, label uniqueness, sequential bootstrap and time-decay weights.", [
    ("Overlapping outcomes and label uniqueness", 2,
     "Why labels that span overlapping periods are not independent, and how to measure uniqueness.",
     [FML, S, TH], [MLFINLAB]),
    ("Sequential bootstrap", 2,
     "Resample so that overlapping observations are drawn less often.",
     [FML, S, SIM, TH], [MLFINLAB]),
    ("Return attribution and time-decay weights", 2,
     "Weight samples by absolute return and recency when training.",
     [FML, ML, TH], [MLFINLAB]),
])
a5 = chapter("Fractionally Differentiated Features",
    "AFML ch. 5. The stationarity-memory trade-off and fractional differentiation.", [
    ("Stationarity versus memory", 2,
     "Why returns are stationary but memoryless, and prices have memory but are non-stationary.",
     [FML, TS, TH], [SSRN_10REASONS]),
    ("Fractional differentiation and the fixed-width window method", 3,
     "The fractional difference operator, binomial weights and the practical implementation.",
     [FML, TS, TH], [MLFINLAB]),
    ("Python: find the minimum d that passes the ADF test", 2,
     "Sweep d, test stationarity, and plot correlation with the original series to choose the smallest workable d.",
     [FML, TS, PY, PR], [STATSMODELS, MLFINLAB]),
])
a67 = chapter("Ensemble Methods and Cross-Validation in Finance",
    "AFML ch. 6-7. Ensembles under non-IID data, leakage, and purged k-fold with embargo.", [
    ("Bagging versus boosting with overlapping labels", 2,
     "Why bagging is safer than boosting on redundant financial samples; average uniqueness in random forests.",
     [FML, ML, TH], [MLFINLAB]),
    ("Why k-fold fails in finance: leakage", 2,
     "Training and test sets that share overlapping label periods inflate performance.",
     [FML, CV, TH], [SSRN_10REASONS]),
    ("Purged k-fold cross-validation and embargo", 3,
     "Remove training observations whose labels overlap the test period and add an embargo after it.",
     [FML, CV, TH], [MLFINLAB]),
    ("Python: implement PurgedKFold", 3,
     "Write a scikit-learn compatible purged splitter and compare its scores with plain k-fold.",
     [FML, CV, PY, PR], [SKLEARN, MLFINLAB]),
])
a89 = chapter("Feature Importance and Hyper-Parameter Tuning",
    "AFML ch. 8-9. MDI, MDA and single-feature importance, orthogonal features, and tuning with purged CV.", [
    ("MDI, MDA and single feature importance", 3,
     "Three importance methods, their biases and how substitution effects mislead them.",
     [FML, ML, TH], [MLFINLAB]),
    ("Orthogonal features and PCA", 2,
     "Reduce substitution effects by rotating features; using PCA as a sanity check on importance.",
     [FML, LA, TH], [MLFINLAB]),
    ("Tuning with purged CV and log-uniform search distributions", 2,
     "Randomized search over sensible scales without leaking the test set.",
     [FML, CV, ML, TH], [SKLEARN]),
])
a10 = chapter("Bet Sizing",
    "AFML ch. 10. Turning predicted probabilities into position sizes.", [
    ("From predicted probability to position size", 2,
     "Size bets by the confidence of the classifier; the sigmoid and z-statistic approaches.",
     [FML, FIN, TH], [MLFINLAB]),
    ("Averaging active bets and size discretization", 2,
     "Combine overlapping signals and reduce turnover with discretized sizes.",
     [FML, FIN, TH], [MLFINLAB]),
    ("Dynamic bet sizes and limit prices", 1,
     "Adjust sizes as forecasts and prices change.",
     [FML, FIN, TH], [MLFINLAB]),
])
a11 = chapter("Backtesting and Its Dangers",
    "AFML ch. 11, 12 and 14. Backtesting errors, combinatorial purged CV and backtest statistics.", [
    ("Common backtesting errors", 3,
     "Survivorship bias, look-ahead, storytelling, data mining, transaction costs and shorting constraints.",
     [FML, BT, TH], [SSRN_PBO]),
    ("Combinatorial purged cross-validation", 3,
     "Generate many backtest paths from one history to estimate the distribution of performance.",
     [FML, BT, CV, TH], [MLFINLAB]),
    ("Backtest statistics: Sharpe, deflated Sharpe ratio and probability of backtest overfitting", 4,
     "Why the Sharpe ratio inflates with the number of trials and how to correct it.",
     [FML, BT, S, TH], [SSRN_DSR, SSRN_PBO]),
    ("Python: deflated Sharpe ratio for a family of strategies", 3,
     "Backtest many parameter variants, compute the DSR of the best one and see how much of the edge survives.",
     [FML, BT, PY, PR], [NUMPY, SCIPY]),
])
a1516 = chapter("Strategy Risk and Machine Learning Asset Allocation",
    "AFML ch. 15-16. The probability a strategy fails, and hierarchical risk parity.", [
    ("Strategy risk: precision, frequency and probability of failure", 2,
     "Relate betting precision and frequency to the Sharpe ratio and compute the probability of failure.",
     [FML, FIN, S, TH], [QUANTRESEARCH]),
    ("Hierarchical risk parity", 3,
     "Why mean-variance weights are unstable and how clustering the correlation matrix produces robust portfolios.",
     [FML, FIN, LA, TH], [QUANTRESEARCH]),
    ("Python: HRP portfolio on a stock universe", 3,
     "Implement HRP and compare its out-of-sample variance with minimum-variance and equal weights.",
     [FML, FIN, PY, PR], [NUMPY, YFINANCE]),
])
a17 = chapter("Structural Breaks and Feature Engineering",
    "AFML ch. 17-19. Break tests, entropy features and microstructural features, in overview.", [
    ("CUSUM and explosiveness tests", 3,
     "Detect regime changes and bubbles with CUSUM and supremum ADF tests.",
     [FML, TS, TH], [MLFINLAB]),
    ("Entropy and microstructural features", 2,
     "Information-content features and order-flow features from tick data, and what they are used for.",
     [FML, TS, FIN, TH], [MLFINLAB]),
])
a_cap = chapter("Capstone: End-to-End Financial ML Pipeline",
    "Assemble the techniques into one reproducible pipeline and evaluate it honestly.", [
    ("Assemble the pipeline", 8,
     "Dollar bars, fractional differentiation, triple-barrier labels, sample weights, purged CV and bet sizing in one codebase.",
     [FML, PY, PROJ], [MLFINLAB, SKLEARN]),
    ("Evaluate and write up", 4,
     "Report combinatorial-CV results, the deflated Sharpe ratio and transaction-cost sensitivity; document every decision.",
     [FML, BT, PROJ, IV], [SSRN_DSR]),
])

COURSE_5 = course(
    "Financial Machine Learning with López de Prado",
    "Chapters 2-12 and 14-17 of Advances in Financial Machine Learning, one or two chapters per week: data structures, "
    "labeling, sample weights, fractional differentiation, purged cross-validation, feature importance, bet sizing, "
    "backtest statistics and HRP. Read the time series roadmap first.",
    [B_AFML], [
    ("Financial data structures",
     "Notebook building dollar bars from intraday data and comparing them with time bars.", [a2]),
    ("Labeling",
     "Notebook implementing triple-barrier labels with a check of label balance and duration.", [a3]),
    ("Sample weights and fractional differentiation",
     "Uniqueness-based sample weights added to the labels; fractional-differentiation notebook with the minimum d found.", [a4, a5]),
    ("Ensembles and purged cross-validation",
     "A PurgedKFold implementation with a comparison against plain k-fold on the labeled data.", [a67]),
    ("Feature importance and bet sizing",
     "MDI/MDA/SFI importance comparison on the model; a bet-sizing function from predicted probabilities.", [a89, a10]),
    ("Backtesting and its dangers",
     "Deflated Sharpe ratio notebook on a family of strategies; one-page summary of backtesting pitfalls.", [a11]),
    ("Strategy risk, HRP and structural breaks",
     "HRP portfolio notebook with an out-of-sample variance comparison; CUSUM test applied to one series.", [a1516, a17]),
    ("Capstone pipeline",
     "End-to-end pipeline repository with combinatorial-CV results, DSR and a write-up.", [a_cap]),
])

# ================================================================ ROADMAP 6
# Interview readiness: the six additional items, split to fit single weeks
r1a = chapter("Linear Algebra I: Systems, Subspaces and Projections",
    "MIT 18.06 lectures 1-17 with Strang. Elimination, vector spaces and least squares as projection.", [
    ("Vectors, matrices, systems of equations and LU factorization", 3,
     "Elimination, matrix multiplication and inverses.",
     [LA, TH], [MIT1806, STRANG]),
    ("Vector spaces, rank and the four fundamental subspaces", 3,
     "Column space, null space, independence and dimension.",
     [LA, TH], [MIT1806, B1B]),
    ("Orthogonality, projections and least squares", 3,
     "Projection matrices and the normal equations behind linear regression.",
     [LA, REG, TH], [MIT1806, STRANG]),
])
r1b = chapter("Linear Algebra II: Eigenvalues, SVD and Covariance",
    "MIT 18.06 lectures 18-31 with Strang. Eigen-decomposition, positive-definite matrices and the SVD, applied to covariance and PCA.", [
    ("Determinants, eigenvalues, eigenvectors and diagonalization", 4,
     "Characteristic polynomials, eigen-decomposition and matrix powers, with Markov chains as the example.",
     [LA, TH], [MIT1806, B1B]),
    ("Symmetric and positive-definite matrices; covariance matrices", 3,
     "The spectral theorem, positive definiteness tests and why covariance matrices are PSD.",
     [LA, FIN, TH], [MIT1806, STRANG]),
    ("Singular value decomposition and PCA", 3,
     "SVD, low-rank approximation and PCA as SVD of the centered data matrix.",
     [LA, ML, TH], [MIT1806, B1B]),
    ("Python: implement PCA and least squares from scratch with NumPy", 3,
     "Code both with explicit matrix operations and verify against scikit-learn and statsmodels.",
     [LA, PY, PR], [NUMPY, SKLEARN]),
])
r2a = chapter("Brainteasers and Probability Problems",
    "Zhou's green book, chapters 2-4: timed practice on brainteasers and probability questions.", [
    ("Brainteasers", 3,
     "Classic puzzles and the reasoning patterns interviewers look for.",
     [IV, PR], [STAT110]),
    ("Probability theory problems", 5,
     "Conditional probability, expectation tricks, distributions and limit theorems under time pressure.",
     [IV, P, PR], [STAT110, EDX110]),
])
r2b = chapter("Statistics, Stochastic Processes and Mock Interviews",
    "Zhou's green book, chapters 5-6, plus recorded mock interviews.", [
    ("Statistics and regression problems", 4,
     "Estimators, hypothesis tests, regression interpretation and bias-variance questions.",
     [IV, S, REG, PR], [MIT18650]),
    ("Stochastic processes and Markov chain problems", 3,
     "Random walks, hitting times, martingale arguments and stationary distributions.",
     [IV, P, PR], [MIT_PROB]),
    ("Mock interviews: timed sets explained aloud", 4,
     "Solve problems while narrating your reasoning; record and review where explanations break down.",
     [IV, PR], [STAT110]),
])
r3a = chapter("Algorithms Refresher",
    "Medium-difficulty algorithm problems on the patterns quant coding rounds use most.", [
    ("Arrays, hashing, two pointers and sliding window", 4,
     "Medium-difficulty problems on the most common patterns.",
     [CODE, IV, PR], [LEETCODE]),
    ("Trees, graphs, BFS/DFS and dynamic programming", 5,
     "Medium-difficulty problems with attention to complexity analysis.",
     [CODE, IV, PR], [LEETCODE]),
])
r3b = chapter("NumPy and pandas for Live Data Tasks",
    "The data-manipulation fluency tested in live coding sessions.", [
    ("NumPy vectorization and pandas group-by, rolling and merge", 4,
     "Replace loops with vectorized operations; rolling windows, resampling and joins on time-indexed data.",
     [CODE, PY, PR], [NUMPY, PANDAS]),
    ("Live data task practice", 2,
     "Clean a messy price file, align calendars, compute rolling statistics and plot, all within 45 minutes.",
     [CODE, PY, IV, PR], [PANDAS, KAGGLE]),
])
r4 = chapter("Machine Learning Interview Depth",
    "Be able to explain core ML ideas from scratch, out loud, to both ML and non-ML interviewers.", [
    ("Bias-variance, overfitting and regularization from first principles", 3,
     "Derive the decomposition, explain how ridge and lasso trade bias for variance, and diagnose overfitting.",
     [ML, IV, TH], [ISL, ESL]),
    ("Trees, random forests and gradient boosting internals", 3,
     "Split criteria, why forests reduce variance, how boosting fits residuals, and the key hyper-parameters.",
     [ML, IV, TH], [ISL, XGBOOST]),
    ("Validation schemes and why you chose one", 2,
     "Random k-fold versus walk-forward versus purged CV; defend the choice for a given dataset.",
     [ML, CV, IV, TH], [SSRN_10REASONS]),
    ("Explaining a model to a non-ML interviewer", 2,
     "Practice a two-minute plain-language explanation of a model, its inputs, and its failure modes.",
     [ML, IV, PR], [ISL]),
])
r5 = chapter("Finance Vocabulary and Market Basics",
    "Enough market knowledge to follow a trading-floor conversation and frame a model's purpose.", [
    ("Returns, volatility, Sharpe ratio and drawdown", 2,
     "Definitions, annualization conventions and what good values look like.",
     [FIN, TH], [INVESTOPEDIA]),
    ("Long/short, market neutrality, beta and factors", 2,
     "Hedging market exposure, dollar versus beta neutrality and the common risk factors.",
     [FIN, TH], [INVESTOPEDIA, MIT18S096]),
    ("Order books, order types, slippage and transaction costs", 2,
     "Market versus limit orders, the bid-ask spread, market impact and why costs decide strategy viability.",
     [FIN, TH], [INVESTOPEDIA]),
    ("From signal to trade: how a systematic strategy runs", 2,
     "Research, signal generation, portfolio construction, execution and monitoring, and where an ML engineer sits.",
     [FIN, FML, TH], [QUANTRESEARCH]),
])
r6a = chapter("Capstone: Design and Build",
    "One honest project on real market data: fix the protocol first, then build and validate.", [
    ("Choose a question and data; fix the out-of-sample protocol up front", 3,
     "Write down the hypothesis, data sources, validation scheme and success criteria before touching the data.",
     [PROJ, FIN, BT], [KAGGLE, YFINANCE]),
    ("Build and validate with walk-forward testing and realistic costs", 10,
     "Implement features, model and backtest; report results net of costs with uncertainty estimates.",
     [PROJ, PY, ML, BT, FIN], [SKLEARN, PANDAS]),
])
r6b = chapter("Capstone: Write-up, Walkthrough and Final Mock Loop",
    "Make the project reproducible and defensible, then rehearse the whole interview loop.", [
    ("Write-up and reproducible repository", 4,
     "README, environment file, one-command reproduction and a short report with figures.",
     [PROJ, CODE, IV], [KAGGLE]),
    ("Five-minute walkthrough and anticipated critiques", 3,
     "Rehearse explaining the project; prepare answers on leakage, overfitting, costs and what you would do next.",
     [PROJ, IV, PR], [SSRN_DSR]),
    ("Final mock interview loop", 4,
     "One full simulated loop: a probability round, a statistics/ML round, a coding round and the project walkthrough.",
     [IV, PR], [STAT110, LEETCODE]),
])

COURSE_6 = course(
    "Interview Readiness for ML Quant Roles",
    "The six things beyond the core books, one week each: linear algebra (two weeks), timed quant problem practice "
    "(two weeks), coding interviews, ML interview depth, finance vocabulary and a capstone project you can defend (two weeks).",
    [B_ZHOU, B_STRANG], [
    ("Linear algebra: systems, subspaces and projections",
     "18.06 problem sets for lectures 1-17; a derivation of the normal equations from projection.", [r1a]),
    ("Linear algebra: eigenvalues, SVD and covariance",
     "18.06 problem sets for lectures 18-31; NumPy implementations of PCA and least squares verified against libraries.", [r1b]),
    ("Brainteasers and probability problems",
     "At least 80 solved problems from the green book with a log of error patterns.", [r2a]),
    ("Statistics, processes and mock interviews",
     "At least 70 more solved problems; two recorded mock interviews reviewed.", [r2b]),
    ("Algorithms refresher",
     "60 medium LeetCode problems with complexity analysis noted for each.", [r3a]),
    ("Data tasks and finance vocabulary",
     "Three timed pandas data tasks completed; a one-page finance glossary.", [r3b, r5]),
    ("ML interview depth",
     "Written two-minute explanations of five ML concepts, rehearsed aloud.", [r4]),
    ("Capstone: design and build",
     "Protocol document written before modeling; working backtest with out-of-sample, cost-adjusted results.", [r6a]),
    ("Capstone: write-up and final mock loop",
     "Capstone repository with README and report; rehearsed walkthrough; one full mock interview loop completed.", [r6b]),
])

roadmap(
    "ML Quant Research Path",
    "<p>The full path for an ML quant researcher: probability, statistical inference, "
    "machine learning, financial time series, financial machine learning and "
    "interview readiness, one course after another.</p>",
    [COURSE_1, COURSE_2, COURSE_3, COURSE_4, COURSE_5, COURSE_6],
)

# ---------------------------------------------------------------- validation
LIMITS = {
    "curriculum.tag": {"name": 50},
    "curriculum.course": {"name": 255},
    "curriculum.chapter": {"name": 255},
    "curriculum.topic": {"topic_name": 255},
    "library.resource": {"title": 255, "author": 255, "file": 100, "url": 2000, "kind": 20},
    "roadmaps.roadmap": {"name": 255},
}
pks = {}
for o in objs:
    pks.setdefault(o["model"], set()).add(o["pk"])
    for f, mx in LIMITS.get(o["model"], {}).items():
        assert len(o["fields"][f]) <= mx, (o["model"], f, o["fields"][f])
for o in objs:
    f = o["fields"]
    if o["model"] == "curriculum.topic":
        assert f["chapter"] in pks["curriculum.chapter"]
        assert all(r in pks["library.resource"] for r in f["resources"])
        assert all(t in pks["curriculum.tag"] for t in f["tags"])
        assert len(set(f["resources"])) == len(f["resources"]) and len(set(f["tags"])) == len(f["tags"])
    elif o["model"] == "curriculum.course":
        assert all(r in pks["library.resource"] for r in f["resources"])
    elif o["model"] == "curriculum.chapter":
        # every chapter is scheduled exactly once (course() asserts no repeats)
        assert f["course"] in pks["curriculum.course"], f"chapter {f['name']} is not in any course"
        assert f["week"] >= 1 and f["order"] >= 1 and f["deliverable"]
    elif o["model"] == "roadmaps.roadmapcourse":
        assert f["roadmap"] in pks["roadmaps.roadmap"] and f["course"] in pks["curriculum.course"]
seen = set()
for o in objs:
    if o["model"] == "roadmaps.roadmapcourse":
        key = ("rc", o["fields"]["roadmap"], o["fields"]["course"])
    elif o["model"] == "curriculum.tag":
        key = ("tag", o["fields"]["name"])
    else:
        continue
    assert key not in seen, key
    seen.add(key)

objs.sort(key=lambda o: (MODEL_ORDER.index(o["model"]), o["pk"]))
with open(OUTPUT, "w", encoding="utf-8") as fh:
    json.dump(objs, fh, indent=2, ensure_ascii=False)
    fh.write("\n")

print()
for m in MODEL_ORDER:
    print(f"{m:28s} {counters.get(m, 0):4d}")
print(f"{'total objects':28s} {len(objs):4d}")
