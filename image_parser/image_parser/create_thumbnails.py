import os, json
from PIL import Image

def create_thumbnails(f, project, width, height, out_dir):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    results = json.load(f)
    classes = {}
    project = str(project)

    w = int(width / 2)
    h = int(height / 2)

    if not project in results:
        print "No images for project: {}".format(project)

    for image_id, image in results[project].iteritems():
        filename = image['filename']

        for species_id, species in image.iteritems():
            if species_id == "filename":
                continue

            species_dir = os.path.join(out_dir, species_id)
            if not species_id in classes:
                classes[species_id] = True
                os.makedirs(species_dir)

            count = 0
            for loc in species:
                img = Image.open(filename, 'r')

                left = loc['center_x'] - w
                if (left + width) >= img.size[0]:
                    left = img.size[0] - width - 1
                if left < 0:
                    left = 0

                right = left + width
                if right >= img.size[0]:
                    img.close()
                    continue

                top = loc['center_y'] - h
                if (top + height) >= img.size[1]:
                    top = img.size[1] - height - 1
                if top < 0:
                    top = 0

                bottom = top + height
                if bottom >= img.size[1]:
                    img.close()
                    continue

                basename = '{}_{}_{}.png'.format(image_id, species_id, count)
                outfile = os.path.join(species_dir, basename)
                img.crop((left, top, right, bottom)).save(outfile)
                img.close()

                count = count + 1
                print '{} with ({}, {}, {}, {})'.format(basename, left, top, right, bottom)
