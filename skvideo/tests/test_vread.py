from numpy.testing import assert_equal
import numpy as np
import skvideo.io
import skvideo.utils
import skvideo.datasets
import os

# test read twice
def test_vread2x():
    for i in xrange(2):
        videodata = skvideo.io.vread(skvideo.datasets.bigbuckbunny())

def test_vread():
    videodata = skvideo.io.vread(skvideo.datasets.bigbuckbunny())

    T, M, N, C = videodata.shape

    # check the dimensions of the video

    assert_equal(T, 132)
    assert_equal(M, 720)
    assert_equal(N, 1280)
    assert_equal(C, 3)

    # check the numbers

    assert_equal(np.mean(videodata), 109.28332841215979)


# reading/writing consistency checks using yuv420 
def _rawhelper1(backend):
    # reading first time
    bunnyMP4VideoData1 = skvideo.io.vread(skvideo.datasets.bigbuckbunny(), num_frames=1, backend=backend)
    skvideo.io.vwrite("bunnyMP4VideoData_vwrite.yuv", bunnyMP4VideoData1, backend=backend)
    bunnyYUVVideoData1 = skvideo.io.vread("bunnyMP4VideoData_vwrite.yuv", width=1280, height=720, num_frames=1, backend=backend)

    skvideo.io.vwrite("bunnyYUVVideoData_vwrite.yuv", bunnyYUVVideoData1, backend=backend)
    bunnyYUVVideoData2 = skvideo.io.vread("bunnyYUVVideoData_vwrite.yuv", width=1280, height=720, num_frames=1, backend=backend)

    # reading second time, to test whether mutable defaults are set correctly
    bunnyMP4VideoData2 = skvideo.io.vread(skvideo.datasets.bigbuckbunny(), num_frames=1, backend=backend)

    # check the dimensions of the videos

    assert_equal(bunnyMP4VideoData1.shape, (1, 720, 1280, 3))
    assert_equal(bunnyMP4VideoData2.shape, (1, 720, 1280, 3))
    assert_equal(bunnyYUVVideoData1.shape, (1, 720, 1280, 3))
    assert_equal(bunnyYUVVideoData2.shape, (1, 720, 1280, 3))

    t = np.mean((bunnyMP4VideoData1 - bunnyMP4VideoData2)**2)
    assert t == 0, "Possible mutable default error in vread. MSE=%f between consecutive reads." % (t,)


    # here, we have yuv->rgb->yuv->rgb causing 1/3 pixel deviation
    error_threshold = 1
    if backend == "libav":
        # the avconv program has major drift :(
        error_threshold = 2

    t = np.mean((bunnyMP4VideoData1 - bunnyYUVVideoData1)**2)
    assert t < error_threshold, "Unacceptable precision loss (mse=%f) performing vwrite (mp4 data) -> vread (raw data)." % (t,)

    error_threshold = 0.001
    if backend == "libav":
        # the avconv program has major drift :(
        error_threshold = 2

    # this actually has loss due to rgb->yuv420->rgb conversion
    t = np.mean((bunnyYUVVideoData1 - bunnyYUVVideoData2)**2)
    assert t < error_threshold, "Unacceptable precision loss (mse=%f) performing vwrite (raw data) -> vread (raw data)." % (t,)

    os.remove("bunnyMP4VideoData_vwrite.yuv")
    os.remove("bunnyYUVVideoData_vwrite.yuv")


# reading/writing consistency check using real input data and yuv444
def _rawhelper2(backend):
    pipingDict = {"-pix_fmt": "yuvj444p"}

    # reading first time
    bunnyMP4VideoData1 = skvideo.io.vread(skvideo.datasets.bigbuckbunny(), num_frames=1, outputdict=pipingDict.copy(), backend=backend)
    skvideo.io.vwrite("bunnyMP4VideoData_vwrite.yuv", bunnyMP4VideoData1, inputdict=pipingDict.copy(), backend=backend)

    # testing pipeline
    bunnyYUVVideoData1 = skvideo.io.vread("bunnyMP4VideoData_vwrite.yuv", width=1280, height=720, num_frames=1, outputdict=pipingDict.copy(), backend=backend)
    skvideo.io.vwrite("bunnyYUVVideoData_vwrite.yuv", bunnyYUVVideoData1, inputdict=pipingDict.copy(), backend=backend)
    bunnyYUVVideoData2 = skvideo.io.vread("bunnyYUVVideoData_vwrite.yuv", width=1280, height=720, num_frames=1, outputdict=pipingDict.copy(), backend=backend)

    # reading second time, to test whether mutable defaults are set correctly
    bunnyMP4VideoData2 = skvideo.io.vread(skvideo.datasets.bigbuckbunny(), num_frames=1, outputdict=pipingDict.copy(), backend=backend)

    # check the dimensions of the videos

    assert_equal(bunnyMP4VideoData1.shape, (1, 720, 1280, 3))
    assert_equal(bunnyMP4VideoData2.shape, (1, 720, 1280, 3))
    assert_equal(bunnyYUVVideoData1.shape, (1, 720, 1280, 3))
    assert_equal(bunnyYUVVideoData2.shape, (1, 720, 1280, 3))

    t = np.mean((bunnyMP4VideoData1 - bunnyMP4VideoData2)**2)
    assert t == 0, "Possible mutable default error in vread. MSE=%f between consecutive reads." % (t,)

    # this actually has no deviation using yuv444 space
    t = np.mean((bunnyMP4VideoData1 - bunnyYUVVideoData1)**2)
    assert t == 0, "Precision loss (mse=%f) performing vwrite (mp4 data) -> vread (raw data)." % (t,)

    # this actually has no loss due to all work being contained in yuv444 space
    t = np.mean((bunnyYUVVideoData1 - bunnyYUVVideoData2)**2)
    assert t == 0, "Unacceptable precision loss (mse=%f) performing vwrite (raw data) -> vread (raw data)." % (t,)

    os.remove("bunnyMP4VideoData_vwrite.yuv")
    os.remove("bunnyYUVVideoData_vwrite.yuv")

def test_vread_raw1_ffmpeg():
    _rawhelper1("ffmpeg")

def test_vread_raw1_libav():
    _rawhelper1("libav")

def test_vread_raw2_ffmpeg():
    _rawhelper2("ffmpeg")

def test_vread_raw2_libav():
    _rawhelper2("libav")
