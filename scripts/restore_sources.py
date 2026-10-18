"""Restore only this workpack's source cache if transient raw files are missing."""
import tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

if __name__=='__main__':
    archive=ROOT/'data/raw_sources.tar.xz';target=ROOT/'data/raw';target.mkdir(parents=True,exist_ok=True)
    with tarfile.open(archive,'r:xz') as t:
        for member in t.getmembers():
            if not member.isfile() or Path(member.name).name!=member.name:raise ValueError('Unexpected archive member')
            dest=target/member.name
            if not dest.exists():
                source=t.extractfile(member)
                if source is None:raise ValueError('Missing archive bytes')
                dest.write_bytes(source.read())
    print('Source cache restored without overwriting existing files')
