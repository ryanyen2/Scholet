import json
from os import listdir
from os.path import isfile, join


def write_to_json(filename, obj):
    with open(filename, "w") as f:
        json.dump(obj, f)


def get_files_in_dir(dir_path):
    only_files = [
        dir_path + "/" + f for f in listdir(dir_path) if isfile(join(dir_path, f))
    ]
    return only_files


class ExtensibleArray:
    def __init__(self):
        self.array = []

    def set_value(self, index, value):
        current_length = len(self.array)

        if index >= current_length:
            self.array.extend([""] * (index - current_length + 1))

        self.array[index] = value

    def get_value(self, index):
        return self.array[index]

    def get_array(self):
        return self.array
