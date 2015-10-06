from app import sass

def test_sass_compiles():
    '''
    Just build all our SASS files and make sure no errors are thrown.
    '''

    sass.build_files()
