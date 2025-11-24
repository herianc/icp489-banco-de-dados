import time

def stream_data(paragraph):
    for word in paragraph.split(" "):
        yield word + " "
        time.sleep(0.02)