# emacs: -*- mode: python; py-indent-offset: 4; tab-width: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 noet:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the datalad package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Metadata extractor for Datalad's own core storage"""

from datalad.metadata.extractors.base import BaseMetadataExtractor

import logging
lgr = logging.getLogger('datalad.metadata.extractors.datalad_core')
from datalad.log import log_progress

from os.path import join as opj
from os.path import exists

from datalad.support.json_py import load as jsonload
from datalad.support.annexrepo import AnnexRepo
from datalad.coreapi import subdatasets
# use main version as core version
# this must stay, despite being a seemingly unused import, each extractor defines a version
from datalad.metadata.definitions import version as vocabulary_version


class MetadataExtractor(BaseMetadataExtractor):
    _dataset_metadata_filename = opj('.datalad', 'metadata', 'dataset.json')
    _unique_exclude = {"url"}

    def _get_dataset_metadata(self):
        """
        Returns
        -------
        dict
          keys are homogenized datalad metadata keys, values are arbitrary
        """
        fpath = opj(self.ds.path, self._dataset_metadata_filename)
        obj = {}
        if exists(fpath):
            obj = jsonload(fpath, fixup=True)
        if 'definition' in obj:
            obj['@context'] = obj['definition']
            del obj['definition']
        obj['@id'] = self.ds.id
        subdsinfo = [{
            # this version would change anytime we aggregate metadata, let's not
            # do this for now
            #'version': sds['revision'],
            'type': sds['type'],
            'name': sds['gitmodule_name'],
        }
            for sds in subdatasets(
                dataset=self.ds,
                recursive=False,
                return_type='generator',
                result_renderer='disabled')
        ]
        if subdsinfo:
            obj['haspart'] = subdsinfo
        superds = self.ds.get_superdataset(registered_only=True, topmost=False)
        if superds:
            obj['ispartof'] = {
                '@id': superds.id,
                'type': 'dataset',
            }

        return obj

    def _get_content_metadata(self):
        """Get ALL metadata for all dataset content.

        Returns
        -------
        generator((location, metadata_dict))
        """
        log_progress(
            lgr.info,
            'extractordataladcore',
            'Start core metadata extraction from %s', self.ds,
            total=len(self.paths),
            label='Core metadata extraction',
            unit=' Files',
        )
        if not isinstance(self.ds.repo, AnnexRepo):
            for p in self.paths:
                # this extractor does give a response for ANY file as it serves
                # an an indicator of file presence (i.e. a file list) in the
                # content metadata, even if we know nothing but the filename
                # about a file
                yield (p, dict())
            log_progress(
                lgr.info,
                'extractordataladcore',
                'Finished core metadata extraction from %s', self.ds
            )
            return
        valid_paths = None
        if self.paths and sum(len(i) for i in self.paths) > 500000:
            valid_paths = set(self.paths)
        # Availability information
        for file, whereis in self.ds.repo.whereis(
                self.paths if self.paths and valid_paths is None else '.',
                output='full',
                add_key=True
            ).items():
            if file.startswith('.datalad') or valid_paths and file not in valid_paths:
                # do not report on our own internal annexed files (e.g. metadata blobs)
                continue
            log_progress(
                lgr.info,
                'extractordataladcore',
                'Extracted core metadata from %s', file,
                update=1,
                increment=True)
            # pull out proper (public) URLs
            # TODO possibly extend with special remote info later on
            meta = {'url': whereis[remote].get('urls', [])
                    for remote in whereis
                    # "web" remote
                    if remote == "00000000-0000-0000-0000-000000000001" and
                    whereis[remote].get('urls', None)}
            # Also record its key.  Since we used `add_key` above, key
            # should be present in a record for each remote, so we will take
            # just first one.  `add_key` was added to avoid separate call to
            # get_file_key which would need to be ran separately
            if whereis:
                meta['annex-key'] = list(whereis.values())[0]['key']
            yield (file, meta)
        log_progress(
            lgr.info,
            'extractordataladcore',
            'Finished core metadata extraction from %s', self.ds
        )
