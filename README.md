# contact-sheet 𝍖
Quickly generate contact sheets containing thousands of images.

## Installation
```bash
git clone https://github.com/worosom/contact-sheet && cd contact-sheet
pip install -r requirements.txt
```
## Usage
```
python main.py --help
Usage: main.py [OPTIONS]

Options:
  --filelist TEXT       List of paths to image files. Paths must be relative
                        to the path of the filelist.  [required]
  --thumb_size INTEGER  Resolution of the images contained in the contact
                        sheet.
  --output_dest TEXT    Destination of the contact sheet.  [required]
  --help                Show this message and exit.
```
## Example
```
$ cd contact-sheet
$ find ../../example/dir -name "*.jpg" > filelist.txt
$ head < filelist.txt
../../example/dir/0.jpg
../../example/dir/1.jpg
../../example/dir/2.jpg
../../example/dir/3.jpg
../../example/dir/4.jpg
../../example/dir/5.jpg
../../example/dir/6.jpg
../../example/dir/7.jpg
../../example/dir/8.jpg
../../example/dir/9.jpg
$ python main.py --thumb_size 64 --filelist filelist.txt --output_dest ../../example/contactsheet.jpg
100%|██████████████████████████████████████████████████████| 250336/250336 [02:20<00:00, 1780.89it/s]
```
