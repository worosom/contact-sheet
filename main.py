import os
import tempfile
from uuid import uuid4 as uuid
from multiprocessing import Process, Queue, cpu_count

import PIL.Image
import numpy as np
import click
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
            break
        else:
            (x, y), file = item
            image = PIL.Image.open(file)
            image = center_crop(image)
            image = image.resize((thumb_size, thumb_size))
            output_memmap[x, y] = image
    output_memmap.flush()


@click.command()
@click.option('--filelist', type=str, required=True, help='List of paths to image files. Paths must be relative to the path of the filelist.')
@click.option('--thumb_size', type=int, default=256, help='Resolution of the images contained in the contact sheet.')
@click.option('--output_dest', type=str, required=True, help='Destination of the contact sheet.')
def main(filelist, thumb_size, output_dest):
    path = os.path.split(os.path.abspath(filelist))[0]
    files = [os.path.join(path, f.rstrip()) for f in open(filelist)]

    num_columns = int(np.ceil(np.sqrt(len(files))))

    output_size = num_columns * thumb_size
    queue = Queue()
    for i, file in enumerate(files):
        x = i % num_columns
        y = i // num_columns
        x *= thumb_size
        y *= thumb_size
        queue.put(((slice(y, y+thumb_size), slice(x, x+thumb_size)), file))
    queue.put(None)

    with tempfile.TemporaryDirectory() as td:
        output_memmap_fname = os.path.join(td, str(uuid()))
        output_memmap = np.memmap(output_memmap_fname, dtype=np.uint8, mode='w+', shape=(output_size, output_size, 3))
        processes = [Process(target=writer, args=(queue, output_memmap, thumb_size)) for _ in range(cpu_count())]
        for process in processes:
            process.start()
        
        pbar = tqdm(total=len(files))
        while any([process.is_alive() for process in processes]):
            pbar.n = len(files) - (queue.qsize() - 1)
        
        for process in processes:
            process.join()

        PIL.Image.fromarray(output_memmap).save(output_dest)

if __name__ == '__main__':
    main()
