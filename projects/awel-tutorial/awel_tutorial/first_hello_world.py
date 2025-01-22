from dbgpt.core.awel import DAG, MapOperator

with DAG("awel_hello_world") as dag:
    task = MapOperator(map_function=lambda x: print(f"Hello, {x}!"))
task._blocking_call(call_data="world")