import hypertools as hyp
import numpy as np
import pandas as pd
from os.path import join as opj
from warnings import warn
from nltk.corpus import stopwords
from PIL.Image import open as open_image


DATADIR= '../../data'
RAWDIR = opj(DATADIR, 'raw')
PARTICIPANTS_DIR = opj(DATADIR, 'participants')
TRAJS_DIR = opj(DATADIR, 'trajectories')
EMBS_DIR = opj(DATADIR, 'embeddings')
MODELS_DIR = opj(DATADIR, 'models')
N_PARTICIPANTS = 50
STOP_WORDS = stopwords.words('english') + ["even", "I'll", "I'm", "let", "let's",
                                           "really", "they'd", "they're",
                                           "they've", "they'll", "that's"]


class Experiment:
    def __init__(self):
        self.lectures = ['Four Forces', 'Birth of Stars']
        self.n_participants = N_PARTICIPANTS
        self.participants = None
        self.avg_participant = None
        self.forces_transcript = None
        self.bos_transcript = None
        self.questions = None
        self.lecture_wsize = 15
        self.forces_windows = None
        self.bos_windows = None
        self.forces_traj = None
        self.bos_traj = None
        self.question_vectors = None
        self.answer_vectors = None
        self.embedding_space = None
        self.forces_embedding = None
        self.bos_embedding = None
        self.question_embeddings = None
        self.wordle_mask = None
        self.cv = None
        self.cv_params = {
            'strip_accents': 'unicode',
            'stop_words': STOP_WORDS
        }
        self.lda = None
        self.lda_params = {
            'n_components': 25,
            'learning_method': 'batch',
            'random_state': 0
        }
        self.umap_reducer = None
        self.umap_params = {
            'n_components': 2,
            'n_neighbors': 15,
            'min_dist': 0.7,
            'spread': 1.0,
            'random_state': 0
        }

    def get_lecture_traj(self, lecture):
        if hasattr(lecture, '__iter__') and not isinstance(lecture, str):
            if len(lecture) > 1:
                return [self.get_lecture_traj(l) for l in lecture]
            else:
                return self.get_lecture_traj(lecture[0])
        elif lecture in ['forces', 1]:
            return self.forces_traj
        elif lecture in ['bos', 2]:
            return self.bos_traj
        else:
            raise ValueError("Lecture should be either 1, 'forces', 2, or 'bos'")

    def get_question_vecs(self, qids=None, lectures=None):
        # get question topic vectors by question ID(s) or lecture(s)
        if (qids is lectures is None) or (qids is not None and lectures is not None):
            raise ValueError("must pass either qids or lecture (not both)")
        if lectures is not None:
            qids = []
            if 'forces' in lectures:
                qids += list(range(15))
            if 'bos' in lectures:
                qids += list(range(15, 30))
            if 'general' in lectures:
                qids += list(range(30, 39))
        else:
            qids = [qid - 1 for qid in qids]
        return self.question_vectors[qids]

    def plot(
            self,
            lectures=None,
            questions=None,
            participants=None,
            keys=None,
            **kwargs
    ):
        """
        Wraps hypertools.plot for multi-subject plots and plotting
        lectures/questions. Plotting order is:
            1. lectures (if multiple, plotted in order passed)
            2. questions (plotted in order passed)
            3. traces (for each participant, in order passed, the trace given by
                each key, in order passed)
        :param lectures: str, int, or iterable of strs/ints (optional)
                Lecture topic trajectories to plot
        :param questions: str, int, or iterable of str/int (optional)
                If str or iterable of strs, the category of questions ("forces",
                "bos", "general") to plot. If int or iterable of ints, the IDs
                of questions to plot
        :param participants: str, int or iterable of strs/ints (optional)
                The participant(s) in `self.participants` whose reconstructed
                traces (given by keys arg) to plot.  May also be "all" for all
                participants or "avg" for `self.avg_participant`
        :param keys: str or iterable of str (required if passing `participants`)
                The keys of reconstructed traces to plot for each participant
        :param kwargs: various types
                Keyword arguments passed to `hypertools.plot`, then forwarded to
                matplotlib
        :return: plot: hypertools.datageometry.DataGeometry
                A plot of the specified data
        """
        if (participants is not None) and (keys is None):
            raise ValueError("Must pass keys if passing participants")
        # funnel args into iterables
        if lectures is None:
            lectures = []
        elif isinstance(lectures, str):
            lectures = [lectures]
        if questions is None:
            questions = []
        elif isinstance(questions, (str, int)):
            questions = [questions]
        if participants is None:
            participants = []
        elif isinstance(participants, str):
            if participants == 'all':
                participants = self.participants
            elif participants == 'avg':
                participants = [self.avg_participant]
            else:
                participants = [participants]
        elif isinstance(participants, int):
            participants = [f'P{participants}']
        if isinstance(keys, str):
            keys = [keys]
        skip_keys = []
        for key in keys:
            if not ('forces' in key or 'bos' in key):
                warn(f"couldn't determine corresponding lecture for trace key "
                     f"'{key}'. Trace will be excluded from plot")
        keys = [k for k in keys if k not in skip_keys]

        to_plot = [self.get_lecture_traj(l) for l in lectures]
        for q in questions:
            if isinstance(q, str):
                to_plot.append(self.get_question_vecs(lectures=q))
            else:
                to_plot.append(self.get_question_vecs(qids=q))

        for p in participants:
            if isinstance(p, int):
                p = f"P{p}"
            if isinstance(p, str):
                p = self.participants[self.participants == p][0]
            for key in keys:
                lec = 'forces' if 'forces' in key else 'bos'
                lec_traj = self.get_lecture_traj(lec)
                trace = p.get_trace(key)
                # weight each timepoint of lecture by knowledge
                to_plot.append(lec_traj * trace[:, np.newaxis])

        return hyp.plot(to_plot, **kwargs)

    ##########################################
    #              DATA LOADERS              #
    ##########################################
    def load_participants(self, load_avg=False):
        participants = []
        for pid in range(1, self.n_participants + 1):
            path = opj(PARTICIPANTS_DIR, f'P{pid}.npy')
            p = np.load(path, allow_pickle=True).item()
            participants.append(p)
        self.participants = np.array(participants)
        if load_avg:
            self.load_avg_participant()
            return self.participants, self.avg_participant
        return self.participants

    def load_avg_participant(self):
        path = opj(PARTICIPANTS_DIR, 'avg.npy')
        self.avg_participant = np.load(path, allow_pickle=True).item()
        return self.avg_participant

    def save_participants(self, filepaths=None, allow_overwrite=False):
        if filepaths is None:
            filepaths = [None] * (len(self.participants) + 1)
        if len(filepaths) != len(self.participants) + 1:
            raise ValueError("`filepaths` should contain one path per "
                             "participant (including average participant, last)")
        for p, fpath in zip(list(self.participants) + [self.avg_participant], filepaths):
            p.save(filepath=fpath, allow_overwrite=allow_overwrite)

    def load_transcript(self, lecture, splitlines=False):
        if isinstance(lecture, str):
            if lecture not in ('forces', 'bos'):
                raise ValueError("lecture may be one of: 'forces', 'bos'")
            path = opj(RAWDIR, f'{lecture}_transcript_timestamped.txt')
            with open(path, 'r') as f:
                transcript = f.read()
            if lecture == 'forces':
                self.forces_transcript = transcript
            else:
                self.bos_transcript = transcript
            if splitlines:
                transcript = transcript.splitlines()
        elif hasattr(lecture, '__iter__'):
            transcript = []
            for l in lecture:
                transcript.append(self.load_transcript(l, splitlines=splitlines))
        else:
            raise ValueError("lecture should be either a str or an iterable of strs")
        return transcript

    def load_questions(self):
        path = opj(RAWDIR, 'questions.tsv')
        self.questions = pd.read_csv(
            path,
            sep='\t',
            names=['index', 'lecture', 'question', 'A', 'B', 'C', 'D'],
            index_col='index'
        )
        return self.questions

    def load_windows(self, lecture):
        if hasattr(lecture, '__iter__') and not isinstance(lecture, str):
            windows = []
            for l in lecture:
                windows.append(self.load_windows(l))
        elif lecture not in ('forces', 'bos'):
            raise ValueError("lecture may be one of: 'forces', 'bos'")
        else:
            windows = np.load(opj(RAWDIR, f'{lecture}_windows.npy'))
            if lecture == 'forces':
                self.forces_windows = windows
            else:
                self.bos_windows = windows
        return windows

    def load_lecture_trajs(self):
        self.forces_traj = np.load(opj(TRAJS_DIR, 'forces_lecture.npy'))
        self.bos_traj = np.load(opj(TRAJS_DIR, 'bos_lecture.npy'))
        return self.forces_traj, self.bos_traj

    def load_question_vectors(self):
        self.question_vectors = np.load(opj(TRAJS_DIR, 'all_questions.npy'))
        return self.question_vectors

    def load_answer_vectors(self):
        self.answer_vectors = np.load(opj(TRAJS_DIR, 'all_answers.npy'))
        return self.answer_vectors

    def load_embeddings(self):
        self.forces_embedding = np.load(opj(EMBS_DIR, 'forces_lecture.npy'))
        self.bos_embedding = np.load(opj(EMBS_DIR, 'bos_lecture.npy'))
        self.question_embeddings = np.load(opj(EMBS_DIR, 'questions.npy'))
        return self.forces_embedding, self.bos_embedding, self.question_embeddings

    def load_cv(self):
        self.cv = np.load(opj(MODELS_DIR, 'fit_CV.npy'), allow_pickle=True).item()
        return self.cv

    def load_lda(self):
        self.lda = np.load(opj(MODELS_DIR, 'fit_LDA.npy'), allow_pickle=True).item()
        return self.lda

    def load_umap(self):
        self.umap_reducer = np.load(opj(MODELS_DIR, 'fit_UMAP.npy'), allow_pickle=True).item()
        return self.umap_reducer

    def load_wordle_mask(self, path=None):
        if path is None:
            path = opj(DATADIR, 'wordle-mask.jpg')
        self.wordle_mask = np.array(open_image(path))
        return self.wordle_mask
