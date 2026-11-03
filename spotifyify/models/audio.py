"""Spotify audio response models; see schemas/source.json and docs/models.md."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field, RootModel

from .base import SpotifyModel
from .common import MusicalKeyValue, TimeSignatureValue

if TYPE_CHECKING:
    from .common import Confidence, Mode1


class Meta(SpotifyModel):
    analyzer_version: str | None = Field(
        None,
        description="The version of the Analyzer used to analyze this track.",
        examples=["4.0.0"],
    )
    platform: str | None = Field(
        None,
        description="The platform used to read the track's audio data.",
        examples=["Linux"],
    )
    detailed_status: str | None = Field(
        None,
        description="A detailed status code for this track. If analysis data is missing, this code may explain why.",
        examples=["OK"],
    )
    status_code: int | None = Field(
        None,
        description="The return code of the analyzer process. 0 if successful, 1 if any errors occurred.",
        examples=[0],
    )
    timestamp: int | None = Field(
        None,
        description="The Unix timestamp (in seconds) at which this track was analyzed.",
        examples=[1495193577],
    )
    analysis_time: float | None = Field(
        None,
        description="The amount of time taken to analyze this track.",
        examples=[6.93906],
    )
    input_process: str | None = Field(
        None,
        description="The method used to read the track's audio data.",
        examples=["libvorbisfile L+R 44100->22050"],
    )


class TimeInterval(SpotifyModel):
    start: float | None = Field(
        None,
        description="The starting point (in seconds) of the time interval.",
        examples=[0.49567],
    )
    duration: float | None = Field(
        None,
        description="The duration (in seconds) of the time interval.",
        examples=[2.18749],
    )
    confidence: Confidence | None = Field(
        None,
        description="The confidence, from 0.0 to 1.0, of the reliability of the interval.",
        examples=[0.925],
    )


class Segment(SpotifyModel):
    start: float | None = Field(
        None,
        description="The starting point (in seconds) of the segment.",
        examples=[0.70154],
    )
    duration: float | None = Field(
        None,
        description="The duration (in seconds) of the segment.",
        examples=[0.19891],
    )
    confidence: Confidence | None = Field(
        None,
        description="The confidence, from 0.0 to 1.0, of the reliability of the segmentation. Segments of the song which are difficult to logically segment (e.g: noise) may correspond to low values in this field.\n",
        examples=[0.435],
    )
    loudness_start: float | None = Field(
        None,
        description='The onset loudness of the segment in decibels (dB). Combined with `loudness_max` and `loudness_max_time`, these components can be used to describe the "attack" of the segment.',
        examples=[-23.053],
    )
    loudness_max: float | None = Field(
        None,
        description='The peak loudness of the segment in decibels (dB). Combined with `loudness_start` and `loudness_max_time`, these components can be used to describe the "attack" of the segment.',
        examples=[-14.25],
    )
    loudness_max_time: float | None = Field(
        None,
        description='The segment-relative offset of the segment peak loudness in seconds. Combined with `loudness_start` and `loudness_max`, these components can be used to desctibe the "attack" of the segment.',
        examples=[0.07305],
    )
    loudness_end: float | None = Field(
        None,
        description="The offset loudness of the segment in decibels (dB). This value should be equivalent to the loudness_start of the following segment.",
        examples=[0.0],
    )
    pitches: list[Confidence] | None = Field(
        None,
        description="Pitch content is given by a “chroma” vector, corresponding to the 12 pitch classes C, C#, D to B, with values ranging from 0 to 1 that describe the relative dominance of every pitch in the chromatic scale. For example a C Major chord would likely be represented by large values of C, E and G (i.e. classes 0, 4, and 7).\n\nVectors are normalized to 1 by their strongest dimension, therefore noisy sounds are likely represented by values that are all close to 1, while pure tones are described by one value at 1 (the pitch) and others near 0.\nAs can be seen below, the 12 vector indices are a combination of low-power spectrum values at their respective pitch frequencies.\n![pitch vector](/assets/audio/Pitch_vector.png)\n",
        examples=[[0.212, 0.141, 0.294]],
    )
    timbre: list[float] | None = Field(
        None,
        description="Timbre is the quality of a musical note or sound that distinguishes different types of musical instruments, or voices. It is a complex notion also referred to as sound color, texture, or tone quality, and is derived from the shape of a segment’s spectro-temporal surface, independently of pitch and loudness. The timbre feature is a vector that includes 12 unbounded values roughly centered around 0. Those values are high level abstractions of the spectral surface, ordered by degree of importance.\n\nFor completeness however, the first dimension represents the average loudness of the segment; second emphasizes brightness; third is more closely correlated to the flatness of a sound; fourth to sounds with a stronger attack; etc. See an image below representing the 12 basis functions (i.e. template segments).\n![timbre basis functions](/assets/audio/Timbre_basis_functions.png)\n\nThe actual timbre of the segment is best described as a linear combination of these 12 basis functions weighted by the coefficient values: timbre = c1 x b1 + c2 x b2 + ... + c12 x b12, where c1 to c12 represent the 12 coefficients and b1 to b12 the 12 basis functions as displayed below. Timbre vectors are best used in comparison with each other.\n",
        examples=[[42.115, 64.373, -0.233]],
    )


class TimeSignature(RootModel[TimeSignatureValue]):
    root: TimeSignatureValue = Field(
        ...,
        description='An estimated time signature. The time signature (meter) is a notational convention to specify how many beats are in each bar (or measure). The time signature ranges from 3 to 7 indicating time signatures of "3/4", to "7/4".',
        examples=[4],
    )


class Tempo(RootModel[float]):
    root: float = Field(
        ...,
        description="The overall estimated tempo of a track in beats per minute (BPM). In musical terminology, tempo is the speed or pace of a given piece and derives directly from the average beat duration.\n",
        examples=[118.211],
    )


class Loudness(RootModel[float]):
    root: float = Field(
        ...,
        description="The overall loudness of a track in decibels (dB). Loudness values are averaged across the entire track and are useful for comparing relative loudness of tracks. Loudness is the quality of a sound that is the primary psychological correlate of physical strength (amplitude). Values typically range between -60 and 0 db.\n",
        examples=[-5.883],
    )


class Key(RootModel[MusicalKeyValue]):
    root: MusicalKeyValue = Field(
        ...,
        description="The key the track is in. Integers map to pitches using standard [Pitch Class notation](https://en.wikipedia.org/wiki/Pitch_class). E.g. 0 = C, 1 = C♯/D♭, 2 = D, and so on. If no key was detected, the value is -1.\n",
        examples=[9],
    )


class Mode(RootModel[int]):
    root: int = Field(
        ...,
        description="Mode indicates the modality (major or minor) of a track, the type of scale from which its melodic content is derived. Major is represented by 1 and minor is 0.\n",
        examples=[0],
    )


class AudioAnalysisTrack(SpotifyModel):
    num_samples: int | None = Field(
        None,
        description="The exact number of audio samples analyzed from this track. See also `analysis_sample_rate`.",
        examples=[4585515],
    )
    duration: float | None = Field(
        None, description="Length of the track in seconds.", examples=[207.95985]
    )
    sample_md5: str | None = Field(
        None, description="This field will always contain the empty string."
    )
    offset_seconds: int | None = Field(
        None,
        description="An offset to the start of the region of the track that was analyzed. (As the entire track is analyzed, this should always be 0.)",
        examples=[0],
    )
    window_seconds: int | None = Field(
        None,
        description="The length of the region of the track was analyzed, if a subset of the track was analyzed. (As the entire track is analyzed, this should always be 0.)",
        examples=[0],
    )
    analysis_sample_rate: int | None = Field(
        None,
        description="The sample rate used to decode and analyze this track. May differ from the actual sample rate of this track available on Spotify.",
        examples=[22050],
    )
    analysis_channels: int | None = Field(
        None,
        description="The number of channels used for analysis. If 1, all channels are summed together to mono before analysis.",
        examples=[1],
    )
    end_of_fade_in: float | None = Field(
        None,
        description="The time, in seconds, at which the track's fade-in period ends. If the track has no fade-in, this will be 0.0.",
        examples=[0.0],
    )
    start_of_fade_out: float | None = Field(
        None,
        description="The time, in seconds, at which the track's fade-out period starts. If the track has no fade-out, this should match the track's length.",
        examples=[201.13705],
    )
    loudness: Loudness | None = None
    tempo: Tempo | None = None
    tempo_confidence: Confidence | None = Field(
        None,
        description="The confidence, from 0.0 to 1.0, of the reliability of the `tempo`.",
        examples=[0.73],
    )
    time_signature: TimeSignature | None = None
    time_signature_confidence: Confidence | None = Field(
        None,
        description="The confidence, from 0.0 to 1.0, of the reliability of the `time_signature`.",
        examples=[0.994],
    )
    key: Key | None = None
    key_confidence: Confidence | None = Field(
        None,
        description="The confidence, from 0.0 to 1.0, of the reliability of the `key`.",
        examples=[0.408],
    )
    mode: Mode | None = None
    mode_confidence: Confidence | None = Field(
        None,
        description="The confidence, from 0.0 to 1.0, of the reliability of the `mode`.",
        examples=[0.485],
    )
    codestring: str | None = Field(
        None,
        description="An [Echo Nest Musical Fingerprint (ENMFP)](https://academiccommons.columbia.edu/doi/10.7916/D8Q248M4) codestring for this track.",
    )
    code_version: float | None = Field(
        None,
        description="A version number for the Echo Nest Musical Fingerprint format used in the codestring field.",
        examples=[3.15],
    )
    echoprintstring: str | None = Field(
        None,
        description="An [EchoPrint](https://github.com/spotify/echoprint-codegen) codestring for this track.",
    )
    echoprint_version: float | None = Field(
        None,
        description="A version number for the EchoPrint format used in the echoprintstring field.",
        examples=[4.15],
    )
    synchstring: str | None = Field(
        None,
        description="A [Synchstring](https://github.com/echonest/synchdata) for this track.",
    )
    synch_version: float | None = Field(
        None,
        description="A version number for the Synchstring used in the synchstring field.",
        examples=[1.0],
    )
    rhythmstring: str | None = Field(
        None,
        description="A Rhythmstring for this track. The format of this string is similar to the Synchstring.",
    )
    rhythm_version: float | None = Field(
        None,
        description="A version number for the Rhythmstring used in the rhythmstring field.",
        examples=[1.0],
    )


class Section(SpotifyModel):
    start: float | None = Field(
        None,
        description="The starting point (in seconds) of the section.",
        examples=[0.0],
    )
    duration: float | None = Field(
        None,
        description="The duration (in seconds) of the section.",
        examples=[6.97092],
    )
    confidence: Confidence | None = Field(
        None,
        description='The confidence, from 0.0 to 1.0, of the reliability of the section\'s "designation".',
        examples=[1.0],
    )
    loudness: float | None = Field(
        None,
        description="The overall loudness of the section in decibels (dB). Loudness values are useful for comparing relative loudness of sections within tracks.",
        examples=[-14.938],
    )
    tempo: float | None = Field(
        None,
        description="The overall estimated tempo of the section in beats per minute (BPM). In musical terminology, tempo is the speed or pace of a given piece and derives directly from the average beat duration.",
        examples=[113.178],
    )
    tempo_confidence: Confidence | None = Field(
        None,
        description="The confidence, from 0.0 to 1.0, of the reliability of the tempo. Some tracks contain tempo changes or sounds which don't contain tempo (like pure speech) which would correspond to a low value in this field.",
        examples=[0.647],
    )
    key: int | None = Field(
        None,
        description="The estimated overall key of the section. The values in this field ranging from 0 to 11 mapping to pitches using standard Pitch Class notation (E.g. 0 = C, 1 = C♯/D♭, 2 = D, and so on). If no key was detected, the value is -1.",
        examples=[9],
    )
    key_confidence: Confidence | None = Field(
        None,
        description="The confidence, from 0.0 to 1.0, of the reliability of the key. Songs with many key changes may correspond to low values in this field.",
        examples=[0.297],
    )
    mode: Mode1 | None = Field(
        None,
        description='Indicates the modality (major or minor) of a section, the type of scale from which its melodic content is derived. This field will contain a 0 for "minor", a 1 for "major", or a -1 for no result. Note that the major key (e.g. C major) could more likely be confused with the minor key at 3 semitones lower (e.g. A minor) as both keys carry the same pitches.',
    )
    mode_confidence: Confidence | None = Field(
        None,
        description="The confidence, from 0.0 to 1.0, of the reliability of the `mode`.",
        examples=[0.471],
    )
    time_signature: TimeSignature | None = None
    time_signature_confidence: Confidence | None = Field(
        None,
        description="The confidence, from 0.0 to 1.0, of the reliability of the `time_signature`. Sections with time signature changes may correspond to low values in this field.",
        examples=[1.0],
    )


class AudioAnalysis(SpotifyModel):
    meta: Meta | None = None
    track: AudioAnalysisTrack | None = None
    bars: list[TimeInterval] | None = Field(
        None,
        description="The time intervals of the bars throughout the track. A bar (or measure) is a segment of time defined as a given number of beats.",
    )
    beats: list[TimeInterval] | None = Field(
        None,
        description="The time intervals of beats throughout the track. A beat is the basic time unit of a piece of music; for example, each tick of a metronome. Beats are typically multiples of tatums.",
    )
    sections: list[Section] | None = Field(
        None,
        description="Sections are defined by large variations in rhythm or timbre, e.g. chorus, verse, bridge, guitar solo, etc. Each section contains its own descriptions of tempo, key, mode, time_signature, and loudness.",
    )
    segments: list[Segment] | None = Field(
        None,
        description="Each segment contains a roughly conisistent sound throughout its duration.",
    )
    tatums: list[TimeInterval] | None = Field(
        None,
        description="A tatum represents the lowest regular pulse train that a listener intuitively infers from the timing of perceived musical events (segments).",
    )
