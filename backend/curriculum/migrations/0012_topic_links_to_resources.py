"""Topic links become Resources (kind + title + url); the Link model is removed.

Every Link becomes one URL-only Resource (or reuses an existing Resource with
the same URL), and every topic keeps exactly the links it had.
"""

from urllib.parse import urlsplit

from django.db import migrations, models

# url -> (title, kind, author) for the links in the seed curriculum.
KNOWN = {
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


def describe(url):
    """(title, kind, author) for a URL; unknown URLs get a title from the address."""
    if url in KNOWN:
        return KNOWN[url]
    parts = urlsplit(url)
    host = (parts.hostname or url).removeprefix("www.")
    path = parts.path.strip("/")
    kind = "code" if host == "github.com" else "other"
    title = f"{host}/{path}" if path else host
    return title[:255], kind, ""


def forwards(apps, schema_editor):
    Link = apps.get_model("curriculum", "Link")
    Resource = apps.get_model("library", "Resource")
    for link in Link.objects.order_by("pk"):
        resource = Resource.objects.filter(url=link.url).order_by("pk").first()
        if resource is None:
            title, kind, author = describe(link.url)
            resource = Resource.objects.create(
                title=title, kind=kind, author=author, url=link.url
            )
        for topic in link.topics.all():
            topic.resources.add(resource)


def backwards(apps, schema_editor):
    """Recreate Links from the URL resources attached to topics."""
    Link = apps.get_model("curriculum", "Link")
    Topic = apps.get_model("curriculum", "Topic")
    for topic in Topic.objects.prefetch_related("resources"):
        for resource in topic.resources.all():
            if resource.url:
                link, _ = Link.objects.get_or_create(url=resource.url)
                topic.links.add(link)


class Migration(migrations.Migration):

    dependencies = [
        ("curriculum", "0011_resources"),
        ("library", "0002_book_to_resource"),
    ]

    operations = [
        migrations.AddField(
            model_name="topic",
            name="resources",
            field=models.ManyToManyField(
                blank=True, related_name="topics", to="library.resource"
            ),
        ),
        migrations.RunPython(forwards, backwards),
        migrations.RemoveField(model_name="topic", name="links"),
        migrations.DeleteModel(name="Link"),
    ]
