from map_saver.models import SavedMap
from map_saver.templatetags.admin_gallery_tags import existing_maps

from django.test import Client
from django.test import TestCase

class SavedMapTest(TestCase):

    def setUp(self):

        """ Create a map
        """

        self.saved_map = SavedMap(**{
            'urlhash': 'abc123',
            'mapdata': '{"global": {"lines": {"0896d7": {"displayName": "Blue Line"}}}, "1": {"1": {"line": "0896d7"}, "2": {"line": "0896d7"}}, "2": {"1": {"line": "0896d7"}}, "3": {"1": {"line": "0896d7"}}, "4": {"1": {"line": "0896d7"}, "2": {"line": "0896d7"}}}'
        })
        self.saved_map.save()

    def confirm_gallery_presence(self, visible):

        """ Helper function to DRY this test;
            Confirms that .publicly_visible and actual gallery presence are the same
        """
        self.saved_map.save()
        self.saved_map.refresh_from_db()

        client = Client()
        response = client.get('/gallery/')
        self.assertEqual(visible, self.saved_map.publicly_visible)
        if visible:
            self.assertContains(response, 'Cool Map')
        else:
            self.assertNotContains(response, 'Cool Map')

    def test_publicly_visible(self):

        """ Confirm that a map is only publicly visible
            when ALL of the following conditions are met:

                .gallery_visible = True
                .name is not blank
                .thumbnail is not blank
                and it has at least one tag in PUBLICLY_VISIBLE_TAGS

            If any of those conditions stop being true,
            the map should stop being publicly visible upon .save()
        """

        self.confirm_gallery_presence(False)

        assignments = {
            'gallery_visible': True,
            'name': 'Cool Map',
            'thumbnail': 'Thumbnail',
        }

        # Even after all of these, I still don't have the tag
        for key, value in assignments.items():
            setattr(self.saved_map, key, value)
            self.confirm_gallery_presence(False)

        self.saved_map.tags.add('irrelevant')
        self.confirm_gallery_presence(False)

        # This tag is good, so now my map is finally publicly visible
        self.saved_map.tags.add('real')
        self.confirm_gallery_presence(True)

        # Any of these is sufficient to make the map no longer publicly visible
        negative_assignments = {
            'gallery_visible': False,
            'name': ' ',
            'thumbnail': ' ',
        }
        for key, value in negative_assignments.items():
            setattr(self.saved_map, key, value)
            self.confirm_gallery_presence(False)

            # But let's put it back the way it was and confirm we're visible again
            setattr(self.saved_map, key, assignments[key])
            self.confirm_gallery_presence(True)

        # Addding the 'reviewed' tag makes it no longer visible
        self.saved_map.tags.add('reviewed')
        self.confirm_gallery_presence(False)

        # Remove the 'reviewed' tag and it's visible again
        self.saved_map.tags.remove('reviewed')
        self.confirm_gallery_presence(True)

        # Finally, remove the 'real' tag and confirm it's no longer visible
        self.saved_map.tags.remove('real')
        self.confirm_gallery_presence(False)

        # Maliciously set publicly_visible = True, save, and confirm it's unset
        self.saved_map.publicly_visible = True
        self.confirm_gallery_presence(False)        

    def test_existing_maps(self):

        """ Confirm the |existing_maps template filter
            returns the correct numbers
        """

        for count in range(1, 11):
            saved_map = SavedMap(**{
                'name': 'test_existing_maps',
                'gallery_visible': True,
                'thumbnail': 'test_existing_maps',
                'urlhash': 'abc123',
                'mapdata': '{"global": {"lines": {"0896d7": {"displayName": "Blue Line"}}}, "1": {"1": {"line": "0896d7"}, "2": {"line": "0896d7"}}, "2": {"1": {"line": "0896d7"}}, "3": {"1": {"line": "0896d7"}}, "4": {"1": {"line": "0896d7"}, "2": {"line": "0896d7"}}}',
            })
            saved_map.save()

            saved_map.refresh_from_db()
            saved_map.tags.add('real')
            saved_map.save()

            self.assertEqual(count, existing_maps(saved_map, 'real'))
