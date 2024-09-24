import os
import tempfile
from uuid import uuid4 as uuid
from threading import Thread
from multiprocessing import Process, Queue, cpu_count
import time

import click
import PIL.Image
import numpy as np
import spacefill.curvetools as curvetools
from tqdm import tqdm


def center_crop(image):
    w, h = image.size
    if w == h:
        return image
    cropbox = (
        w / 2 - h / 2 if w > h else 0,
        h / 2 - w / 2 if h > w else 0,
        w / 2 + h / 2 if w > h else w,
        h / 2 + w / 2 if h > w else h,
    )
    return image.crop(cropbox)


def writer(queue: Queue, output_memmap: np.memmap, thumb_size: int):
    while True:
        item = queue.get()
        if item == None:
            queue.put(None)
            queue.close()
            break
        else:
            (x, y), file = item
            image = PIL.Image.open(file)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            if image.size[0] != image.size[1]:
                image = center_crop(image)
            image = image.resize((thumb_size, thumb_size))
            output_memmap[x, y] = image
    output_memmap.flush()


def make_queue_item(i, fpath, num_columns, thumb_size, curve_map, hilbert):
    if hilbert:
        x, y = curvetools.position_to_coord(i / num_columns**2, curve_map)
        x = int(x)
        y = int(y)
    else:
        x = i % num_columns
        y = i // num_columns
    x *= thumb_size
    y *= thumb_size
    return ((slice(y, y+thumb_size), slice(x, x+thumb_size)), fpath)

num_queued = 0

@click.command()
@click.option('--filelist', type=str, required=True, help='List of paths to image files. Paths must be relative to the path of the filelist.')
@click.option('--output_dest', type=str, required=True, help='Destination of the contact sheet.')
@click.option('--thumb_size', type=int, show_default=True, default=256, help='Resolution of the images contained in the contact sheet.')
@click.option('--hilbert', is_flag=True, show_default=True, default=False, help='')
def main(filelist, thumb_size, output_dest, hilbert):
    path = os.path.split(os.path.abspath(filelist))[0]
    files = [os.path.join(path, f.rstrip()) for f in open(filelist)]

    num_columns = int(np.ceil(np.sqrt(len(files))))
    curve_map = curvetools.generate_map(num_columns, num_columns)

    output_size = num_columns * thumb_size
    queue = Queue(cpu_count())

    total = len(files)
    pbar = tqdm(total=total)

    def add_to_queue():
        global num_queued
        for i, fpath in enumerate(files):
            queue_item = make_queue_item(i, fpath, num_columns, thumb_size, curve_map, hilbert)
            queue.put(queue_item)
            num_queued += 1
        queue.put(None)

    queue_thread = Thread(target=add_to_queue)
    queue_thread.start()

    with tempfile.TemporaryDirectory() as td:
        output_memmap_fname = os.path.join(td, str(uuid()))
        output_memmap = np.memmap(output_memmap_fname, dtype=np.uint8, mode='w+', shape=(output_size, output_size, 3))
        processes = [Process(target=writer, args=(queue, output_memmap, thumb_size)) for _ in range(cpu_count() // 2)]
        for process in processes:
            process.start()

        while any([process.is_alive() for process in processes]):
            pbar.n = num_queued - queue.qsize() + 1
            pbar.update(0)
            time.sleep(1)

        for process in processes:
            process.join()

        queue_thread.join()
        queue.close()

        PIL.Image.fromarray(output_memmap).save(output_dest)

if __name__ == '__main__':
    main()
