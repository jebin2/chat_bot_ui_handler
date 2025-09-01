from setuptools import setup, find_packages

setup(
	name="chat-bot-ui-handler",
    version="0.1.0",
	packages=find_packages(exclude=["test*"]),
	install_requires=[
		"python-dotenv",
		"json-repair",
		"custom_logger @ git+https://github.com/jebin2/custom_logger.git",
		"browser_manager @ git+https://github.com/jebin2/browser_manager.git"
	],
    author="Jebin Einstein",
    author_email="jebineinstein@gmail.com",
    description="A package for automating various chatbot UI interactions",
	long_description=open("README.md").read(),
	long_description_content_type="text/markdown",
	url="https://github.com/jebin2/chat_bot_ui_handler",  # Your repo URL
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",  # Choose a license
		"Operating System :: OS Independent",
	],
	python_requires=">=3.7",  # Specify minimum Python version
)