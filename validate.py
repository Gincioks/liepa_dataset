from os import walk
from os.path import join, splitext, split, normpath
from re import compile
from argparse import ArgumentParser
import wave
import contextlib
import codecs
import chardet

txt_extensions = ['.txt', '.TXT']
wav_extensions = ['.wav', '.WAV']

default_wav_framerate = 22050

age_groups = {
    'c', (12, 12),
    'd', (13, 13),
    'e', (14, 14),
    'f', (15, 15),
    'g', (16, 16),
    'h', (17, 17),
    'i', (18, 18),
    'j', (19, 19),
    'k', (20, 20),
    'l', (21, 25),
    'm', (26, 30),
    'n', (31, 40),
    'o', (41, 50),
    'p', (51, 60),
    'r', (61, -1)  # over 61
    }

valid_symbols = u'AĄBCČDEĘĖFGHIĮJKLMNOPQRSŠTUŲŪVWXYZŽaąbcčdeęėfghiįjklmnopqrsštuųūvwxyzž!\'(),-.:;? _'
valid_utf8_symbol_set = set(valid_symbols.encode('utf-8'))
valid_utf16_symbol_set = set(valid_symbols.encode('utf-16'))
valid_utf8_sig_symbol_set = set(valid_symbols.encode('UTF-8-SIG'))
valid_windows_1257_symbols_set = set(valid_symbols.encode('windows-1257') + b'\x9a')

pattern = compile(r'(?P<type>ZS?|SS?)?(?P<voice>\d+)(?P<sex>M|V)(?P<age>[a-r])_(?P<ut_id>(?P<ut_id_d>\d+)[abc]?)(_(?P<ut_subid>\d+[abc]?))?(?P<tag>_[TP])?(?P<ext>\.(wav|txt))')

# Some files have incorrect utterance type indicator, parent directories indicate correctly.
known_utterance_type_naming_exceptions = [
    ('D57', 'S007'), ('D57', 'S008'),
    ('D556', 'S013'), ('D556', 'S014'),
    ('D556', 'Z000'), ('D556', 'Z001'),
    ('D556', 'Z020'), ('D556', 'Z060')
    ]

known_voice_directory_file_naming_exceptions = range(2, 100)

known_voice_naming_exceptions = [('D251', 'Z026'), ('D515', 'S012'), ('D515', 'Z000'), ('D516', 'S012')]

def wav_duration(path):
    with contextlib.closing(wave.open(path,'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        return (frames / float(rate)), frames, rate

def collect_audio_sampling_problems(file_path):
    duration, frames, framerate = wav_duration(file_path)

    _, filename = split(file_path)

    if default_wav_framerate != framerate:
        problem = '"%s" has %d framerate, default is %d.' % (filename, framerate, default_wav_framerate)
        return [(file_path, framerate, default_wav_framerate, problem)]

    return []

def collect_encoding_problems(file_path):
    text = None
    try:
        with open(file_path, 'rb') as f:
            raw_text = f.read()

        raw_text_symbol_set = set(raw_text) - set('\x1f')

        diff_win_1257 = raw_text_symbol_set - valid_windows_1257_symbols_set
        diff_utf_16 = raw_text_symbol_set - valid_utf16_symbol_set
        diff_utf_8_sig = raw_text_symbol_set - valid_utf8_sig_symbol_set
        diff_utf_8 = raw_text_symbol_set - valid_utf8_symbol_set

        if len(diff_win_1257) == 0:
            charenc = 'windows-1257'
        elif len(diff_utf_16) == 0:
            charenc = 'utf-16'
        elif len(diff_utf_8) == 0:
            charenc = 'utf-8'
        elif len(diff_utf_8_sig) == 0:
            charenc = 'UTF-8-SIG'
        else:
            result = chardet.detect(raw_text)
            charenc = result['encoding']

            if charenc in [
                'Windows-1254', 'windows-1251',
                'Windows-1252', 'ISO-8859-1',
                'ISO-8859-9']:
                charenc = 'windows-1257'

        if charenc == 'windows-1257':
            text = raw_text.replace(b'\x9a', b'\xfe').decode(charenc).replace('\t', ' ')
        else:
            text = raw_text.decode(charenc).replace('\t', ' ')

        diff_set = set(text) - set(valid_symbols)

        if len(diff_set) > 0:
            raise Exception()

        if charenc != 'utf-8':
            problem = '"%s" has %s encoding but utf-8 is required.' % (file_path, charenc)
            return [(file_path, charenc, 'utf-8', problem)]
    except Exception as e:
        return [(file_path, 'undefined', 'utf-8', str(e))]
    return []

def cleanup_naming_problems(naming_problems):
    clean_naming_problems = []

    for src, dst, comment in naming_problems:
        duplicate = False
        for src_, dst_, _ in clean_naming_problems:
            if src == src_:
                if dst == dst_:
                    duplicate = True
                else:
                    raise Exception('Problems have multiple solutions:\n\t%s > %s\n\t%s > %s' % (src, dst, src, src_))
        if not duplicate:
            clean_naming_problems.append((src, dst, comment))
    return clean_naming_problems

def cleanup_sampling_problems(sampling_problems):
    clean_sampling_problems = []

    for path, src_framerate, dst_framerate, comment in sampling_problems:
        duplicate = False
        for path_, src_framerate_, dst_framerate_, _ in clean_sampling_problems:
            if path == path_:
                if src_framerate == src_framerate_ and dst_framerate == dst_framerate_:
                    duplicate = True
                else:
                    raise Exception('Sampling problems have multiple solutions: %s, %s.' % (path, path_))
        if not duplicate:
            clean_sampling_problems.append((path, src_framerate, dst_framerate, comment))

    return clean_sampling_problems

def cleanup_encoding_problems(encoding_problems):
    clean_encoding_problems = []

    for path, src_enc, dst_enc, comment in encoding_problems:
        duplicate = False
        for path_, src_enc_, dst_enc_, _ in clean_encoding_problems:
            if path == path_ and src_enc == src_enc_ and dst_enc == dst_enc_:
                duplicate = True
        if not duplicate:
            clean_encoding_problems.append((path, src_enc, dst_enc, comment))

    return clean_encoding_problems

def validate_static_value(static_name, voice, static, test):
    if not test:
        raise Exception('%s can not be %s for speaker "%s".' % (static_name, test, voice))
    elif static and static != test:
        raise Exception('%s "%s" for speaker "%s" does not match prvious "%s".' % (static_name, test, voice, static))

    return test

def collect_problems(dataset_path, skip_encoding_test, skip_framerate_test):
    encoding_problems = []
    sampling_problems = []
    naming_problems = []
    layering_problems = []

    for root, subdirs, files in walk(dataset_path):
        age_group = None
        gender = None

        root = normpath(root)
        path, leaf = split(root)
        if path == '':
            continue

        dir_group = None
        if leaf[0] in ['D', '.']:
            path = root
        else:
            dir_group = leaf
            utternace_group_type = dir_group[0]

            if utternace_group_type not in ['Z', 'S']:
                raise Exception('Utternace type "%s" does not match valid pattern.' % utternace_group_type)

        db_root, voice = split(path)

        if voice[0] != 'D':
            raise Exception('Voice name "%s" does not start with "D".' % voice[0])

        voice_id = voice[1:]
        correct_voice_id  = '%03d' % int(voice_id)
        if voice_id != correct_voice_id:
            problem = 'Voice id is "%s" but should be "%s".' % (voice_id, correct_voice_id)
            if int(voice_id) not in known_voice_directory_file_naming_exceptions:
                raise Exception(problem)
            else:
                correct_voice_path = join(db_root, 'D' + correct_voice_id)
                naming_problems.append((path, correct_voice_path, problem))

        for filename in files:
            match = pattern.match(filename)
            if not match:
                raise Exception('Filename "%s" does not match valid pattern.' % filename)
            else:
                name, _extension = splitext(filename)

                if dir_group:
                    group = dir_group
                    file_path = join(path, group, filename)
                else:
                    group = match.group('type') + match.group('ut_id_d')

                    file_path = join(path, filename)
                    fixed_dir = join(path, group)
                    fixed_file_path = join(fixed_dir, filename)
                    utternace_group_type = match.group('type')

                    problem = 'File "%s" is missing group "%s" folder.' % (file_path, group)
                    layering_problems.append((file_path, fixed_dir, fixed_file_path, problem))

                if _extension in wav_extensions and not skip_framerate_test:
                    sampling_problems += collect_audio_sampling_problems(file_path)
                    pass

                if _extension in txt_extensions and not skip_encoding_test:
                    encoding_problems += collect_encoding_problems(file_path)
                    pass

                tag = match.group('tag') # _T or _P
                if not tag:
                    tag = ''

                utterance_sub_id = match.group('ut_subid')
                if not utterance_sub_id:
                    utterance_sub_id = ''

                gender = validate_static_value('Gender', voice, gender, match.group('sex'))
                age_group = validate_static_value('Age group', voice, age_group, match.group('age'))

                utternace_id = match.group('ut_id')

                correct_filename = '%s%s%s%s_%s_%s%s%s' % (utternace_group_type, correct_voice_id, gender, match.group('age'), utternace_id, utterance_sub_id, tag, match.group('ext'))
                correct_file_path = join(path, group, correct_filename)

                if voice_id != match.group('voice'):
                    problem = 'Voice id "%s" does not match with id "%s" from filename "%s".' % (voice_id, match.group('voice'), file_path)
                    can_continue = False
                    for exc in  known_voice_naming_exceptions:
                        if voice == exc[0] and group == exc[1]:
                            can_continue = True
                            naming_problems.append((file_path, correct_file_path, problem))

                    if not can_continue and int(voice_id) not in known_voice_directory_file_naming_exceptions:
                        raise Exception(problem)

                if match.group('type') != utternace_group_type:
                    problem = 'Utterance group "%s" for "%s" voice is of type "%s", but utterance "%s" is of type "%s". Path: "%s".' % (group, voice, utternace_group_type, filename, match.group(1), root)
                    can_continue = False
                    for exc in known_utterance_type_naming_exceptions:
                        if voice == exc[0] and group == exc[1]:
                            can_continue = True
                            naming_problems.append((file_path, correct_file_path, problem))

                    if not can_continue:
                        raise Exception(problem)

    return (
        cleanup_encoding_problems(encoding_problems),
        cleanup_sampling_problems(sampling_problems),
        layering_problems,
        cleanup_naming_problems(naming_problems))

if __name__ == '__main__':

    default_dir = './MII_LIEPA_V1'

    parser = ArgumentParser()
    parser.add_argument('-d','--liepa-dir', help='LIEPA dataset directory (Default: "%s").' % default_dir, default=default_dir)
    parser.add_argument('-e','--skip-encoding-test', help='Skip LIEPA dataset transcript encoding testing.', action='store_true')
    parser.add_argument('-f','--skip-framerate-test', help='Skip LIEPA dataset audio framerate testing.', action='store_true')
    args = parser.parse_args()

    result = collect_problems(args.liepa_dir, args.skip_encoding_test, args.skip_framerate_test)

    encoding_problems, sampling_problems, layering_problems, naming_problems = result

    # DO ENCODING CORRECTIONS BEFORE FILE RENAMING OR MOVING
    for path, src_enc, dst_enc, comment in encoding_problems:
        print ('Change encoding from %s to %s encoding for "%s". %s' % (src_enc, dst_enc, path, comment))

    # DO RESAMPLING BEFORE FILE RENAMING OR MOVING
    for path, src_framerate, dst_framerate, comment in sampling_problems:
        print ('Resample "%s" from %d to %d fps. %s' % (path, src_framerate, dst_framerate, comment))

    # Layering files and directories
    for src, dst_dir, dst, comment in layering_problems:
        print ('MKDIR "%s" and MOVE "%s" to "%s". %s' % (dst_dir, src, dst, comment))

    # Rename files
    for src, dst, comment in naming_problems:
        print ('Rename "%s" to "%s". %s' % (src, dst, comment))
