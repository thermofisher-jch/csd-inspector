from glob import glob

def check_version(path):
    version = os.path.join(path, 'version.txt')
    if os.path.exists(version):
        with open(version) as f:
            line = f.readline()
        return line.startswith('Torrent_Suite=3')
    return False

def add_if_exists(tar, path):
    if os.path.exists(path):
        tar.add(path)
        return True
    return False

root = '/opt/lemontest/deployment/files'

def add_files(tar, path):
    path = os.path.relpath(path, root)
    if not check_version(path):
        return False
    files = [
        'explog_final.txt',
        'InitLog*.txt',
        'version.txt',
        'sigproc_results',
        'basecaller_results',
    ]
    added = False
    for filename in files:
        p = os.path.join(path, filename)
        for name in glob(p):
            added = add_if_exists(tar, name) or added
    return added


tar = tarfile.open("/home/lemonadmin/2013-08-12_inspector_copy.tar.gz", "w:gz")

f = open("/home/lemonadmin/2013-08-12_inspector_copy.csv", 'w')

for row in rows:
    if add_files(tar, row[2]):
        f.write("\t".join([str(row[0]), row[1], os.path.basename(row[2])])+"\n")
        print("Added %d" % row[0])
tar.close()
f.close()
