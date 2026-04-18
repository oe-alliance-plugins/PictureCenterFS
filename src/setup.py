from setuptools import setup
import setup_translate

pkg = 'Extensions.PictureCenterFS'
setup(name='enigma2-plugin-extensions-picturecenterfs',
       version='1.0',
       description='PictureCenterFS',
       package_dir={pkg: 'PictureCenterFS'},
       packages=[pkg],
       package_data={pkg: ['skin/pictures/*.png', 'skin/*.xml', 'skin/fHD/*.xml', 'skin/fHD/pictures/*.png', 'skin/HD/*.xml', 'skin/HD/pictures/*.png', '*.png', '*.xml', 'locale/*/LC_MESSAGES/*.mo', 'LICENSE', 'maintainer.info']},
       cmdclass=setup_translate.cmdclass,  # for translation
      )
