build_linux: clean
	docker run -v "$(pwd):/src/" cdrx/pyinstaller-linux "pyinstaller --clean --onedir --add-data "ops;ops" --add-data /home/shyft/stuff/miniconda3/lib/python3.9/site-packages/pyppeteer-0.2.5.dist-info:pyppeteer-0.2.5.dist-info casper_agent.py"

	cd dist
	tar cvzf casper_agent_linux.tar.gz linux/
	cd ..

build_windows: clean
	# https://github.com/cdrx/docker-pyinstaller
	# docker run -v "$(pwd):/src/" cdrx/pyinstaller-windows 'pyinstaller -y --onedir --add-data "ops;ops" --add-data "C:\python37\Lib\site-packages\pyppeteer-0.2.5.dist-info;pyppeteer-0.2.5.dist-info" --add-data "config.toml;." casper_agent.py'
	
	# https://github.com/pyppeteer/pyppeteer/issues/213#issuecomment-854693247
	pyinstaller -y --onedir --add-data "ops;ops" --copy-metadata pyppeteer --add-data "config.toml;." casper_agent.py # should word
	
	#pyinstaller -y --onedir --add-data "ops;ops" --add-data "C:\\Users\\IEUser\\AppData\\Local\\Programs\\Python\\Python39\\lib\\site-packages\pyppeteer-0.2.5.dist-info;pyppeteer-0.2.5.dist-info" --add-data "config.toml;." casper_agent.py	
	cd dist
	zip -r casper_agent_windows.zip windows/
	cd ..
	
pip_install:
	pip install -r requirements.txt

clean:
	rm -rf dist build 

