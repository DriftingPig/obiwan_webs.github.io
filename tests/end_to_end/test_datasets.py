# tests datasets DR3, DR5, DR3_eBOSS

from __future__ import print_function
import os
import matplotlib.pyplot as plt
import numpy as np

import fitsio
import photutils

from astrometry.libkd.spherematch import match_radec
from astrometry.util.fits import fits_table
from legacypipe.survey import LegacySurveyData, wcs_for_brick

from obiwan.kenobi import main,get_parser
from obiwan.qa.visual import plotImage, readImage

DATASETS= ['DR3','DR5','DR3_eBOSS']


def run_dataset(dataset):
    """run a single dataset's test problem

    Args:
        dataset: string, 'DR3', 'DR5', etc
    """
    assert(dataset in DATASETS)
    print('testing dataset: %s' % dataset)
    obj='elg'
    brick='1238p245'
    os.environ["LEGACY_SURVEY_DIR"]= os.path.join(os.path.dirname(__file__), 
                                                  'legacypipedir_%s_dataset_%s' % (brick,dataset))
    outdir = os.path.join(os.path.dirname(__file__),
                          'outdir_%s_%s' % (brick,dataset))
    randoms_from_fits= os.path.join(os.path.dirname(__file__), 
                                    'randoms/%s' % obj,'randoms_%s_10.fits' % brick)

    cmd_line=['--dataset', dataset, '-b', brick, '-n', '2', 
              '-o', 'elg', '--outdir', outdir, '--add_sim_noise',
              '--randoms_from_fits', randoms_from_fits]
    parser= get_parser()
    args = parser.parse_args(args=cmd_line)

    main(args=args)
    assert(True)



#fn = os.path.join(outdir, 'tractor', '110', 'tractor-1102p240.fits')
#assert(os.path.exists(fn))
#T = fits_table(fn)
#assert(len(T) == 2)
#print('Types:', T.type)
#assert(T.type[0] == 'REX ')
#cmd = ('(cd %s && sha256sum -c %s)' %
#       (outdir, os.path.join('tractor', '110', 'brick-1102p240.sha256sum')))
#print(cmd)
#rtn = os.system(cmd)
#assert(rtn == 0)

def test_dataset_DR3():
    run_dataset('DR3')
    assert(True)

def test_dataset_DR5():
    run_dataset('DR5')
    assert(True)


class Testcase(object):
    """Initialize and run a testcase

    Args:
        name: testcase name
        dataset: string, 'DR3', 'DR5', etc
        zoom: the zoom array pass to runbrick
        all_blobs,add_noise: booleans
    """
    def __init__(self, name='testcase_DR5_z',dataset='DR5',
                 all_blobs=False,add_noise=True):
        assert(dataset in DATASETS)
        self.name= name
        self.dataset= dataset
        self.all_blobs= all_blobs
        self.add_noise= add_noise
        self.outname= 'out_'+self.name
        if self.all_blobs:
            self.outname += '_allblobs'
        if self.add_noise:
            self.outname += '_addnoise'
        self.outdir= os.path.join(os.path.dirname(__file__), 
                                  self.outname)
        
        if '_grz' in self.name:
            self.brick='0285m165' 
            self.bands= ['g','r','z']
            self.zoom= [3077, 3277, 2576, 2776]
        else:
            self.brick='1741p242'
            self.bands= ['z']
            self.zoom= [90, 290, 2773, 2973]

        os.environ["LEGACY_SURVEY_DIR"]= os.path.join(os.path.dirname(__file__), 
                                                      self.name)
         
    def run(self):
        """run it"""
        print('Running testcase: %s' % self.name)
        extra_cmd_line = []
        if self.add_noise:
            extra_cmd_line += ['--add_sim_noise']
        if self.all_blobs:
            extra_cmd_line += ['--all_blobs']

        randoms_from_fits= os.path.join(os.environ["LEGACY_SURVEY_DIR"], 
                                        'randoms.fits')

        cmd_line=['--dataset', self.dataset, '-b', self.brick, '-n', '4', 
                  '--zoom', str(self.zoom[0]), str(self.zoom[1]), 
                            str(self.zoom[2]), str(self.zoom[3]),
                  '-o', 'elg', '--outdir', self.outdir,
                  '--randoms_from_fits', randoms_from_fits] + extra_cmd_line
        parser= get_parser()
        args = parser.parse_args(args=cmd_line)

        main(args=args)


class AnalyzeTestcase(Testcase):
    """Automatically loads the relevant outputs for a given testcase_DR_*

    Args:
        name: like 'testcase_DR5_z_allblobs'

    Attributes:
        brick:
        bands:
        zoom:
        brickwcs:
    """
    def __init__(self, **kwargs):
        super(AnalyzeTestcase, self).__init__(**kwargs)

        # Tolerances
        if '_grz' in self.name:
            self.tol={'apsims_p_apsky_m_aptractor':0.2, #nanomags
                      'simcat_p_apsky_m_aptractor':0.3}
        else:
            if self.add_noise:
                self.tol={'apsims_p_apsky_m_aptractor':0.2, 
                          'simcat_p_apsky_m_aptractor':0.7}
            else:
                self.tol={'apsims_p_apsky_m_aptractor':0.2, 
                          'simcat_p_apsky_m_aptractor':0.5}

        survey = LegacySurveyData()
        brickinfo = survey.get_brick_by_name(self.brick)
        self.brickwcs = wcs_for_brick(brickinfo)

        self.outdir= os.path.join(os.environ['HOME'],
                           'myrepo/obiwan/tests/end_to_end',
                            self.outname,'elg/%s/%s/rs0/' % \
                             (self.brick[:3],self.brick)
                         )
    
    def load_outputs(self):
        """Each output from the testcase becomes an attribute

        Attributes:
            simcat, obitractor:
            jpg_coadds:
            fits_coadds
        """
        print('Loading from %s' % self.outdir)
        self.simcat= fits_table(os.path.join(self.outdir,'obiwan/simcat-elg-%s.fits' % self.brick))
        self.obitractor= fits_table(os.path.join(self.outdir,'tractor/tractor-%s.fits' % self.brick))

        self.blobs= fitsio.FITS(os.path.join(self.outdir,'metrics/blobs-%s.fits.gz' % self.brick))[0].read()

        self.img_jpg= readImage(os.path.join(self.outdir,'coadd/legacysurvey-%s-image.jpg' % self.brick),
                           jpeg=True)
        self.model_jpg= readImage(os.path.join(self.outdir,'coadd/legacysurvey-%s-model.jpg' % self.brick),
                             jpeg=True)
        self.resid_jpg= readImage(os.path.join(self.outdir,'coadd/legacysurvey-%s-resid.jpg' % self.brick),
                             jpeg=True)

        self.img_fits,self.ivar_fits,self.sims_fits= {},{},{}
        for b in self.bands:
            self.img_fits[b]= readImage(os.path.join(self.outdir,'coadd/legacysurvey-%s-image-%s.fits.fz' % \
                                             (self.brick,b)))
            self.ivar_fits[b]= readImage(os.path.join(self.outdir,'coadd/legacysurvey-%s-invvar-%s.fits.fz' % \
                                              (self.brick,b)))
            self.sims_fits[b]= readImage(os.path.join(self.outdir,'coadd/legacysurvey-%s-sims-%s.fits.fz' % \
                                              (self.brick,b)))
            
    def simcat_xy(self):
        """x,y of each simulated source in the fits coadd. Just like the
            bx,by of tractor catalogues
        """
        _,x,y=self.brickwcs.radec2pixelxy(self.simcat.ra,self.simcat.dec)
        self.simcat.set('x',x - self.zoom[0])
        self.simcat.set('y',y - self.zoom[2])

    def match_simcat_tractor(self):
        """matches sim and real sources to tractor cat

        Returns:
            isim,itrac: indices into simcat,tractor 
            ireal: inices into tractor
        """
        # sims to tractor
        rad= 10. * self.brickwcs.pixel_scale() / 3600 #deg
        isim,itrac,d= match_radec(self.simcat.ra, self.simcat.dec, 
                                  self.obitractor.ra, self.obitractor.dec,          
                                  rad,nearest=True)
        # real galaxy to tractor 
        ra_real,dec_real= self.brickwcs.pixelxy2radec(
                                [self.zoom[0] + 100.],
                                [self.zoom[2] + 100.])
        _,ireal,d= match_radec(ra_real, dec_real, 
                               self.obitractor.ra, self.obitractor.dec,          
                               rad,nearest=True)
        return isim,itrac,ireal

    def plots(self):
        """outdir: where write plots to """
        fig,ax=plt.subplots(2,2,figsize=(6,6))
        plotImage().imshow(self.blobs,ax[0,0],qs=None)
        plotImage().imshow(self.img_jpg,ax[0,1],qs=None)
        plotImage().imshow(self.model_jpg,ax[1,0],qs=None)
        plotImage().imshow(self.resid_jpg,ax[1,1],qs=None)
        fn=os.path.join(self.outdir,'blob_img_mod_res.png')
        plt.savefig(fn,dpi=150)
        print('Wrote %s' % fn)
        plt.close()

        fig,ax=plt.subplots(3,3,figsize=(7,6))
        for i,b in enumerate(self.bands) :
            plotImage().imshow(self.img_fits[b],ax[0,i])
            plotImage().imshow(self.sims_fits[b],ax[1,i],qs=None)
            plotImage().circles(self.obitractor.bx,self.obitractor.by,ax[1,i],
                                img_shape=self.sims_fits[b].shape,
                                r_pixels=5./0.262,color='y')
            plotImage().circles(self.simcat.x,self.simcat.y,ax[1,i],
                                img_shape=self.sims_fits[b].shape,
                                r_pixels=4./0.262,color='m')
            plotImage().imshow(self.img_fits[b] - self.sims_fits[b],ax[2,i])
        fn=os.path.join(self.outdir,'fits_coadd_img_sims_res.png')
        plt.savefig(fn,dpi=150)
        print('Wrote %s' % fn)
        plt.close()

    def numeric_tests(self):
        """T: TestcaseOutputs() object """
        isim,itrac,ireal= self.match_simcat_tractor()
        assert((len(isim) == 4) & (len(itrac) == 4))
        if self.all_blobs:
            assert(len(ireal) ==1) # found the real galaxy
        else:
            if '_grz' in self.name:
                assert(len(ireal) == 1) # central galaxy in blob on a sim
            else:
                assert(len(ireal) == 0)

        # Tractor apflux is nearly bang on to my apflux for sims coadd 
        # plus my apflux for sky in coadd
        # However, Tractor model flux is does not agree with fits coadd counts
        # so its computing on something else and is currently wrong for sim sources
        apers= photutils.CircularAperture((self.simcat.x,self.simcat.y), 
                                           r=3.5/self.brickwcs.pixel_scale())
        for b in self.bands: 
            apy_table = photutils.aperture_photometry(self.img_fits[b], apers)
            img_apflux= np.array(apy_table['aperture_sum'])
            apy_table = photutils.aperture_photometry(self.sims_fits[b], apers)
            sims_apflux= np.array(apy_table['aperture_sum'])
            sky_apflux= img_apflux - sims_apflux
            # tractor apflux vs. my apflux sims + sky 
            obitractor_apflux= self.obitractor[itrac].get('apflux_'+b)[:,5]
            simcat_flux= self.simcat.get(b+'flux')
            diff= sims_apflux + \
                    sky_apflux - obitractor_apflux
            print(diff) 
            assert(np.all(np.abs(diff) 
                                < self.tol['apsims_p_apsky_m_aptractor'])) 
            # tractor apflux vs. simcat table + sky
            diff= simcat_flux + \
                    sky_apflux - obitractor_apflux
            print(diff,self.add_noise,self.tol['simcat_p_apsky_m_aptractor'])
            assert(np.all(np.abs(diff) 
                                < self.tol['simcat_p_apsky_m_aptractor'])) 
        print('passed')


def test_cases(z=True,
               grz=True):
    """
    Args:
        z_band: z-band testcase?
        grz_band: grz-band testcase?
    """
    # Two: z, grz, Possibly modifications: can add sim galaxies at diff 
    #   seaprations (currnetly 4 sep by 12''), Or can can run w/ or wout/ 
    #   all_blobs, etc
    d= dict(name='testcase_DR5_z',dataset='DR5',
            add_noise=False)
    
    if z:
        for all_blobs in [False]: #,True]:
            d.update(all_blobs=all_blobs)
            T= Testcase(**d)
            T.run()

            A= AnalyzeTestcase(**d)
            A.load_outputs()
            A.simcat_xy()
            A.plots()
            A.numeric_tests()

    if grz:
        d.update(name='testcase_DR5_grz')
        for all_blobs in [True,False]:
            d.update(all_blobs=all_blobs)
            T= Testcase(**d)
            T.run()

            A= AnalyzeTestcase(**d)
            A.load_outputs()
            A.simcat_xy()
            A.plots()
            A.numeric_tests()

def test_main():
    """travis CI"""
    test_cases(z=True,
               grz=False)

if __name__ == "__main__":
    #test_dataset_DR3()
    #test_dataset_DR5() 
    test_cases(z=True,
               grz=False)

    