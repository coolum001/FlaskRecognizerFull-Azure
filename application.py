from flask import render_template
from flask import flash
from flask import redirect
from flask import request
from flask import url_for
from flask import send_from_directory
from flask import session
from werkzeug.utils import secure_filename
from flask import Flask

# import object holding app-specific configuration
from config import Config

# import the specification of forms used, to be included in rendered templates
# note login form not yet used
from forms import LoginForm

from forms import ResponseForm
from forms import UploadForm

from recognizer import Recognizer

import os


import fastai
import fastai.vision
import fastai.metrics
import fastai.basic_train

import torch

# from app import app

app = Flask(__name__)
app.config.from_object(Config)


# home page
@app.route('/')
@app.route('/index')
def index():

    return render_template('index.html')


# end index

# login page - not yet used
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash(
            'Login requested for user {}, remember_me={}'.format(
                form.username.data, form.remember_me.data
            )
        )
        return redirect('/index')
    # end if

    return render_template('login.html', title='Sign In', form=form)


# end login


ALLOWED_EXTENSIONS = set(['jpg', 'png', 'jpeg'])


def allowed_extension(filename):
    '''
    checks a filename for having an extension in the allowed list.
    Allowed list is held in ALLOWED_EXTENSIONS
    '''
    return ('.' in filename) and (
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# end allowed_file


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    form = UploadForm()
    if form.validate_on_submit():
        if request.method == 'POST':
            file = form.photo.data
            if not allowed_extension(file.filename):
                #  File must be a jpg
                exts = ""
                flash(
                    'File name must end in one of: '
                    + ', '.join(ALLOWED_EXTENSIONS)
                    + '. You entered:  '
                    + file.filename
                )
                return redirect(request.url)
            else:
                filename = secure_filename(file.filename)

                # if needed, initialize upload count, else bump count
                if 'upload_count' in session:
                    session['upload_count'] = session['upload_count'] + 1
                else:
                    session['upload_count'] = 1
                # end if

                # report upload success to user, showing file name
                flash('Loading ... ' + filename)
                flash('Saving to ' + app.config['UPLOAD_FOLDER'] + '...')
                filename = file.filename
                file.save(
                    os.path.join(
                        app.instance_path, app.config['UPLOAD_FOLDER'], filename
                    )
                )
                flash('Saved to ' + app.config['UPLOAD_FOLDER'])

                #  run CNN on image
                my_cnn = Recognizer()

                model_path = os.path.join(app.instance_path, app.config['MODEL_FOLDER'])
                image_path = os.path.join(
                    app.instance_path, app.config['UPLOAD_FOLDER'], filename
                )
                guesses = my_cnn.recognize(model_path, image_path)
                flash('Processing complete ...')

                # remove the file, having performed guess process
                try:
                    os.remove(image_path)
                except OSError:
                    pass
                # end try
                flash('File cleanup complete.')

                # Display result to user
                form = ResponseForm()
                return render_template(
                    'ack_upload.html',
                    form=form,
                    filename=filename,
                    uploadcount=str(session['upload_count']),
                    guesses=guesses,
                )
            # end if
        # end if
    # end if
    return render_template('upload.html', title='Upload File', form=form)


# end upload_file


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(
        os.path.join(app.instance_path, app.config['UPLOAD_FOLDER']), filename
    )


# end uploaded_file

