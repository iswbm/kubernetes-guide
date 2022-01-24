import os
import re
import linecache
from glob import glob

pwd = os.getcwd()
source_dir = os.path.join(pwd, "source")


def get_chapter_name(file):
    return linecache.getline(file, 2).strip()


def get_title(file):
    first_line = linecache.getline(file, 1)

    if first_line.startswith("#"):
        return first_line.replace("# ", "").strip()


def get_all_chapter():
    all_chapters_path = []
    os.chdir(source_dir)

    for dir_name in glob("c*"):
        if dir_name == "chapters" or dir_name == "conf.py":
            continue
        all_chapters_path.append(os.path.join(pwd, "source", dir_name))

    all_chapters_path.append(os.path.join(pwd, "source", "extra"))
    return all_chapters_path


def generate_mapping(all_chapters_path):
    mapping = dict.fromkeys([os.path.basename(chapter_path) for chapter_path in all_chapters_path])
    for key in mapping.keys():
        chapter_file = os.path.join(pwd, "source", "chapters", key.replace("c", "p") + ".rst")
        mapping[key] = get_chapter_name(chapter_file)

    mapping["extra"] = "附：加餐分享"
    return mapping


def get_toc_info(all_chapters_path):
    tocs = {}

    for dir_name in all_chapters_path:
        chapter_name = os.path.basename(dir_name)
        tocs.setdefault(chapter_name, [])
        os.chdir(os.path.join(source_dir, dir_name))
        for file_path in sorted(glob(os.path.join(dir_name, "*.md"))):
            file_name = os.path.basename(file_path)

            md_path = os.path.join("https://k8s.iswbm.com/", chapter_name, file_name.replace("md", "html"))
            title = get_title(file_name)
            if not title:
                continue

            tocs[chapter_name].append((title, md_path))

    return tocs


def print_md_toc(tocs, mapping):
    for chapter_name, posts in tocs.items():
        chapter_name = mapping[chapter_name]
        print(f"- **{chapter_name}**")
        for post in posts:
            # print title only 
            # print(f"{post[1][0]}")
            print("  ", f"* [{post[0]}]({post[1]})")


def main():
    all_chapter = get_all_chapter()
    mapping = generate_mapping(all_chapter)
    tocs = get_toc_info(all_chapter)
    print_md_toc(tocs, mapping)


if __name__ == '__main__':
    main()
