from datetime import datetime

import modal

from utils import modal_task, remote_scheduler

stub = modal.Stub(image=modal.DebianSlim().pip_install(["redun", "numpy", "pandas"]))
volume = modal.SharedVolume().persist("redun-db")


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@modal_task(stub=stub, namespace="default", nout=1)
def add(a: float, b: float):
    msg = "{} :: {} + {} = {}".format(now(), a, b, a + b)
    return msg


@modal_task(stub=stub, namespace="default", nout=1)
def mul(a: float, b: float):
    msg = "{} :: {} + {} = {}".format(now(), a, b, a * b)
    return msg


@modal_task(stub=stub, namespace="default", nout=1)
def workflow():

    add_result = add.lazy(a=2.0, b=3.0)
    mul_result = mul.lazy(a=3.0, b=3.0)

    return add_result + "\n" + mul_result


@stub.function(shared_volumes={"/redun": modal.ref("redun-db")})
def run():

    scheduler = remote_scheduler(db_uri="sqlite:////redun/redun.db")
    res = scheduler.run(workflow.lazy())
    print(res)


if __name__ == "__main__":
    with stub.run():
        run()
