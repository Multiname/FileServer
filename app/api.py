from app import app
from .models import db, FileInfo
import json
from flask import request, send_file
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
from win32_setctime import setctime
import calendar

def FindAllFilesInfo():
    return db.session.query(FileInfo).all()

def FindFileInfoById(id):
    return db.session.query(FileInfo).filter(FileInfo.id == id).first()

def FindFileInfoByPath(path, name, extension):
    return db.session.query(FileInfo).filter(FileInfo.name == name).\
                                        filter(FileInfo.extension == extension).\
                                        filter(FileInfo.path == path).first()

def SyncFilePresence(path, name, extension):
    fullpath = os.getcwd() + app.config['UPLOAD_FOLDER'] + path + name + extension

    if os.path.exists(fullpath):
        fileInfo = FileInfo()

        fileInfo.name = name
        fileInfo.extension = extension
        fileInfo.size = os.path.getsize(fullpath)
        fileInfo.path = path
        fileInfo.created_at = datetime.utcfromtimestamp(os.path.getctime(fullpath)) + timedelta(hours=3)

        updated_at = datetime.utcfromtimestamp(os.path.getmtime(fullpath)) + timedelta(hours=3)
        fileInfo.updated_at = updated_at if fileInfo.created_at != updated_at else None

        fileInfo.comment = None

        db.session.add(fileInfo)
        db.session.commit()

        return True, fileInfo
    
    return False, None

def SyncFileAbsence(fileInfo):
    fullpath = os.getcwd() + app.config['UPLOAD_FOLDER'] + \
        fileInfo.path + fileInfo.name + fileInfo.extension

    if not os.path.exists(fullpath):
        db.session.delete(fileInfo)
        db.session.commit()

        return True
    
    return False

def SyncFoldersFilesPresence(folder):
    root = os.getcwd() + app.config['UPLOAD_FOLDER']
    cd = root + folder

    content = os.listdir(cd)
    for obj in content:
        if os.path.isfile(cd + obj):
            name, extension = obj.split('.')
            extension = '.' + extension
            fileInfo = FindFileInfoByPath(folder, name, extension)
            if fileInfo == None:
                SyncFilePresence(folder, name, extension)
        else:
            SyncFoldersFilesPresence(folder + obj + '/')

def SyncFoldersFilesAbsence(folder):
    allFilesInfo = FindAllFilesInfo()
    filesInfo = list(filter(lambda x: x.path.find(folder) == 0, allFilesInfo))

    for fileInfo in filesInfo:
        if not os.path.exists(os.getcwd() + app.config['UPLOAD_FOLDER'] + \
                       fileInfo.path + fileInfo.name + fileInfo.extension):
            db.session.delete(fileInfo)
            db.session.commit()

def SyncFoldersFiles(folder):
    SyncFoldersFilesPresence(folder)
    SyncFoldersFilesAbsence(folder)

def SyncFile(fileInfo, path, name, extension):
    isExisting = False
    if fileInfo == None:
        isExisting, fileInfo = SyncFilePresence(path, name, extension)
        if not isExisting:
            return None
        
    if not isExisting:
        if SyncFileAbsence(fileInfo):
            return None
        
    return fileInfo

def SerializeFileInfo(fileInfo):
    return {
        "name": fileInfo.name,
        "extension": fileInfo.extension,
        "size": fileInfo.size,
        "path": fileInfo.path,
        "created_at": str(fileInfo.created_at),
        "updated_at": str(fileInfo.updated_at) if fileInfo.updated_at != None else None,
        "comment": fileInfo.comment
    }

def SerializeFilesInfo(filesInfo):
    result = []
    for fileInfo in filesInfo:
        result.append(SerializeFileInfo(fileInfo))

    return json.dumps(result)

def HandleFilepath(filepath):
    splited = filepath.split('/')
    index = -1 if splited[-1] != '' else -2
    name, extension = splited[index].split('.')
    extension = '.' + extension
    path = '/' + '/'.join(splited[:index]) + '/'
    if path == '//':
        path = '/'
    return path, name, extension



@app.route('/get_files_info_by_path/', methods=['GET'])
@app.route('/get_files_info/', methods=['GET'])
def get_files_info():
    SyncFoldersFiles('/')

    filesInfo = FindAllFilesInfo()

    return SerializeFilesInfo(filesInfo)

@app.route('/get_files_info_by_path/<path:folderpath>', methods=['GET'])
def get_files_info_by_path(folderpath):
    folderpath = '/' + folderpath
    if folderpath[-1] != '/':
        folderpath += '/'

    SyncFoldersFiles(folderpath)

    allFilesInfo = FindAllFilesInfo()
    filesInfo = list(filter(lambda x: x.path.find(folderpath) == 0, allFilesInfo))

    return SerializeFilesInfo(filesInfo)

@app.route('/get_file_info_by_id/<int:id>', methods=['GET'])
def get_file_info_by_id(id):
    fileInfo = FindFileInfoById(id)
    if fileInfo == None:
        return 'not found', 404
    
    if SyncFileAbsence(fileInfo):
        return 'not found', 404

    return json.dumps(SerializeFileInfo(fileInfo))

@app.route('/get_file_info_by_name/<path:filepath>', methods=['GET'])
def get_file_info_by_name(filepath):
    path, name, extension = HandleFilepath(filepath)

    fileInfo = FindFileInfoByPath(path, name, extension)
    fileInfo = SyncFile(fileInfo, path, name, extension)
    if fileInfo == None:
        return 'not found', 404
    
    return json.dumps(SerializeFileInfo(fileInfo))

@app.route('/upload_file/', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'no file to load', 400

    file = request.files['file']

    if not file:
        return 'no file to load', 400

    root = os.getcwd() + app.config['UPLOAD_FOLDER']
    cd = '/'
    if 'extra_path' in request.form and request.form['extra_path']:
        folders = request.form['extra_path'].split('/')
        for folder in folders:
            folder = secure_filename(folder)

            if folder == '':
                continue

            cd += folder
            folderToCreate = root + cd
            if not os.path.exists(folderToCreate):
                os.mkdir(folderToCreate)
            cd += '/'

    filename = secure_filename(file.filename)
    name, extension = filename.split('.')
    extension = '.' + extension

    path = root + cd + filename
    if os.path.exists(path):
        SyncFilePresence(cd, name, extension)
        return 'file already exists', 400

    fileInfoCheck = FindFileInfoByPath(cd, name, extension)
    if fileInfoCheck != None:
        SyncFileAbsence(fileInfoCheck)

    file.save(path)

    fileInfo = FileInfo()

    fileInfo.name = name
    fileInfo.extension = extension
    fileInfo.size = os.path.getsize(path)
    fileInfo.path = cd
    fileInfo.created_at = datetime.utcfromtimestamp(os.path.getctime(path)) + timedelta(hours=3)
    fileInfo.updated_at = None

    comment = None
    if 'comment' in request.form:
        comment = request.form['comment']
    fileInfo.comment = comment

    db.session.add(fileInfo)
    db.session.commit()
    
    return 'file has been uploaded'

@app.route('/download_file/<path:filepath>', methods=['GET'])
def download_file(filepath):
    path, name, extension = HandleFilepath(filepath)

    fileInfo = FindFileInfoByPath(path, name, extension)
    fileInfo = SyncFile(fileInfo, path, name, extension)
    if fileInfo == None:
        return 'not found', 404

    return send_file(os.getcwd() + app.config['UPLOAD_FOLDER'] + \
                        fileInfo.path + fileInfo.name + fileInfo.extension,
                     as_attachment=True)

@app.route('/delete_file_by_id/', methods=['DELETE'])
def delete_file_by_id():
    content = request.get_json()

    if 'id' not in content:
        return 'no file to delete', 404

    fileInfo = FindFileInfoById(content['id'])
    if fileInfo == None:
        return 'not found', 404
    
    if SyncFileAbsence(fileInfo):
        return 'not found', 404

    os.remove(os.getcwd() + app.config['UPLOAD_FOLDER'] + fileInfo.path + fileInfo.name + fileInfo.extension)

    db.session.delete(fileInfo)
    db.session.commit()

    return 'file has been deleted'

@app.route('/delete_file_by_name/', methods=['DELETE'])
def delete_file_by_name():
    content = request.get_json()

    if 'path' not in content:
        return 'no file to delete', 404

    path, name, extension = HandleFilepath(content['path'])
    fileInfo = FindFileInfoByPath(path, name, extension)
    
    fileInfo = SyncFile(fileInfo, path, name, extension)
    if fileInfo == None:
        return 'not found', 404
    
    os.remove(os.getcwd() + app.config['UPLOAD_FOLDER'] + fileInfo.path + fileInfo.name + fileInfo.extension)

    db.session.delete(fileInfo)
    db.session.commit()

    return 'file has been deleted'

@app.route('/edit_file/', methods=['PUT'])
def edit_file():
    content = request.get_json()

    if 'path' not in content:
        return 'no file to edit'
    
    path, name, extension = HandleFilepath(content['path'])
    fileInfo = FindFileInfoByPath(path, name, extension)
    fileInfo = SyncFile(fileInfo, path, name, extension)
    if fileInfo == None:
        return 'not found', 404
    
    fullpath = os.getcwd() + app.config['UPLOAD_FOLDER'] + fileInfo.path + fileInfo.name + fileInfo.extension
    atime = os.path.getatime(fullpath)
    
    isModified = False
    modifiedPath = os.getcwd() + app.config['UPLOAD_FOLDER'] + \
        fileInfo.path + fileInfo.name + fileInfo.extension

    if 'name' in content and content['name'] != None:
        folder = os.getcwd() + app.config['UPLOAD_FOLDER'] + fileInfo.path
        oldName = folder + fileInfo.name + fileInfo.extension
        newName = folder + secure_filename(content['name']) + fileInfo.extension
        os.rename(oldName, newName)

        setctime(newName, calendar.timegm((fileInfo.created_at - timedelta(hours=3)).utctimetuple()) + \
                 fileInfo.created_at.microsecond / 1000000.0)

        fileInfo.name = secure_filename(content['name'])
        db.session.add(fileInfo)
        db.session.commit()
        isModified = True
        modifiedPath = newName

    if 'folder' in content and content['folder'] != None:
        root = os.getcwd() + app.config['UPLOAD_FOLDER']
        
        folders = content['folder'].split('/')
        cd = root + '/'
        for folder in folders:
            folder = secure_filename(folder)

            if folder == '..' or folder == '':
                continue

            cd += folder + '/'
            if not os.path.exists(cd):
                os.mkdir(cd)

        if content['folder'][0] != '/':
            content['folder'] = '/' + content['folder']
        if content['folder'][-1] != '/':
            content['folder'] += '/'

        oldFolder = root + fileInfo.path + fileInfo.name + fileInfo.extension
        newFolder = root + content['folder'] + fileInfo.name + fileInfo.extension
        os.rename(oldFolder, newFolder)

        setctime(newFolder, calendar.timegm((fileInfo.created_at - timedelta(hours=3)).utctimetuple()) + \
                 fileInfo.created_at.microsecond / 1000000.0)
        
        fileInfo.path = content['folder']
        db.session.add(fileInfo)
        db.session.commit()
        isModified = True
        modifiedPath = newFolder

    if 'comment' in content and content['comment'] != None:
        fileInfo.comment = content['comment']
        db.session.add(fileInfo)
        db.session.commit()
        isModified = True

    if isModified:
        now = datetime.now()

        fileInfo.updated_at = now
        db.session.add(fileInfo)
        db.session.commit()

        utime = calendar.timegm((now - timedelta(hours=3)).utctimetuple())
        utime += now.microsecond / 1000000.0
        os.utime(modifiedPath, (atime, utime))

        return 'file has been updated'
    
    return 'no fields to edit were specified'