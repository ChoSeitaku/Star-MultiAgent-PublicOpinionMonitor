container: dict[str, list] = {}


def subscribe(event_type: str, callback):
    """注册事件类型回调到容器。"""
    if event_type not in container:
        container[event_type] = []
    container[event_type].append(callback)


def tom_wechat(data):
    """Tom 接收事件并打印数据。"""
    print(f"tom收到:{data}")


def jack_wechat(data):
    """Jack 接收事件并打印数据。"""
    print(f"jack收到:{data}")


def publish(event_type: str, data: dict):
    """向指定事件类型回调分发数据。"""
    if event_type in container:
        for callback in container[event_type]:
            callback(data)


subscribe("news", tom_wechat)
subscribe("weather", jack_wechat)
subscribe("news", jack_wechat)

publish("weather", {"content": "今天天气真好", "location": "Beijing"})
