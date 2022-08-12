# About
A very naive attempt at running a `redun` workflow using `Modal` as a backend.

## Redun

[redun](https://github.com/insitro/redun) is a fantastic workflow engine with very a minimal design. 

It let's you write code which looks something like this:

```python
@redun.task
def load() -> pd.DataFrame:
    return pd.DataFrame()


@redun.task
def aggregate(df: pd.DataFrame, method: str) -> pd.DataFrame:
    return df.groupby(...).agg(method)


@redun.task
def plot(data: pd.DataFrame) -> Figure:
    return data.plot.scatter("x", "y")


@redun.task
def analysis():
    df = load_data()
    fig_mean = plot_data(aggregate(df, "mean"))
    fig_median = plot_data(aggregate(df, "median"))
```

It then gives you a few benefits compared to raw python code:
- Smart caching: Each intermediate result is cached, and is only recomputed if either the source code changes, or input arguments change
- Parallelism: `fig_mean` and `fig_median` can be generated in parallel
- Provenance: `redun` takes care of logging the data lineage if you ever need to understand how a given result was produced.

## Modal

[Modal](https://modal.com/docs/guide) "is a new tool that lets you run code in the cloud without having to think about infrastructure."

It essentially allows you to run your code in the cloud with a ridiculously low overhead. 

```python
import modal

stub = modal.Stub(
    image=modal.DebianSlim().pip_install(["numpy", "pandas", "matplotlib"])
)

@stub.function
def load() -> pd.DataFrame:
    return pd.DataFrame()


@stub.function
def aggregate(df: pd.DataFrame, method: str) -> pd.DataFrame:
    return df.groupby(...).agg(method)


@stub.function
def plot(data: pd.DataFrame) -> Figure:
    return data.plot.scatter("x", "y")


@stub.function
def analysis():
    df = load_data()
    fig_mean = plot_data(aggregate(df, "mean"))
    fig_median = plot_data(aggregate(df, "median"))
```

When executed, these functions will almost instantly run in the cloud using the specified environment.

## Modal x Redun

It's tempting to ask the obvious question: can we use `redun` to provide parallelism and caching, but use `Modal` as the execution engine?

Unfortunately it's not as straightforward, 

`Modal` expects that the functions inside the module are truly functions, so something like this will not work (because `foo` is now a `task`, not a function):

```python
# my_module.py

@redun.task
@stub.function
def foo():
    ...
```

`modal` also cannot (currently?) generate functions dynamically, so we cannot write something like

```python
def submit_task(task, stub, *args, **kwargs):
    raw_fn = task.func
    modal_fn = stub.function(raw_fn)
    result = modal_fn(*args, **kwargs)
```

So for this dumb PoC when calling a `task` one needs to write `foo.t(*args)` instead of `foo(*args)`, which is ugly as hell but at least it works.

```python
@modal_task(stub=stub)
def add(x, y):
    return x + y


@modal_task(stub=stub)
def analysis():
    res_1 = add.t(1, 1)
    res_2 = add.t(2, 2)
```

For this PoC we also decided it would be better to run the `redun` scheduler in the cloud, storing the database in a persistent `SharedVolume`

# Setup

Install the `Modal` client package, and then add `redun`: 

```bash
python -m pip install redun
```

# Demo

Running
```bash
python demo.py
```

Will execute the code for the first time, printing out something like:
```
2022-08-12T14:25:19+0000 Execution duration: 7.63 seconds
2022-08-12 14:25:17 :: 2.0 + 3.0 = 5.0
2022-08-12 14:25:17 :: 2.0 + 3.0 = 6.0
```

Re-running the same code again, we will see exactly the same message, since the results are cached:
```
2022-08-12 14:25:17 :: 2.0 + 3.0 = 5.0
2022-08-12 14:25:17 :: 2.0 + 3.0 = 6.0
```

However if we modify the code, e.g. by setting `mul_result = mul.lazy(a=3.0, b=3.0)` one of the results will be updated:
```
2022-08-12 14:25:17 :: 2.0 + 3.0 = 5.0
2022-08-12 14:26:07 :: 3.0 + 3.0 = 9.0
```

Which is exactly what we wanted.