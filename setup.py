from setuptools import setup, find_packages

setup(
    name="face_recognition_system",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'customtkinter',
        'CTkMessagebox',
        'opencv-python',
        'numpy',
        'insightface',
        'onnxruntime',  # Required for insightface
    ],
    entry_points={
        'console_scripts': [
            'face-recognition=src.main:main',
        ],
    },
    python_requires='>=3.8',
)