"""

uses py.test

sudo_easy_install py

http://codespeak.net/py/dist/test.html

"""
import os
import sys
import unittest
from django.conf import settings

TEST_ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(TEST_ROOT + "/..")

sys.path = [ROOT] + sys.path

from hydeengine.file_system import File, Folder
from hydeengine import url
from hydeengine import Initializer, setup_env
from hydeengine.siteinfo import SiteNode, SiteInfo

TEST_SITE = Folder(TEST_ROOT).child_folder("test_site")

def setup_module(module):
    Initializer(TEST_SITE.path).initialize(ROOT, force=True)
    setup_env(TEST_SITE.path)
    
def teardown_module(module):
    TEST_SITE.delete()

class TestSiteInfo:

    def setup_method(self, method):
        self.site = SiteInfo(settings, TEST_SITE.path)        

    def assert_node_complete(self, node, folder):
        assert node.folder.path == folder.path
        test_case = self
        class Visitor(object):
            def visit_folder(self, folder):
                child = node.find_child(folder)
                assert child
                test_case.assert_node_complete(child, folder)
                
            def visit_file(self, a_file):
                assert node.find_resource(a_file)
                
        folder.list(Visitor())

    def test_population(self):
        assert self.site.name == "test_site"
        self.assert_node_complete(self.site, TEST_SITE)
        
    def test_type(self):
        def assert_node_type(node_dir, type):
           node = self.site.find_child(Folder(node_dir))
           assert node
           assert Folder(node_dir).same_as(node.folder)
           for child in node.walk():
               assert child.type == type
        assert_node_type(settings.CONTENT_DIR, "content")
        assert_node_type(settings.MEDIA_DIR, "media")
        assert_node_type(settings.LAYOUT_DIR, "layout")
        
    def test_attributes(self):
        for node in self.site.walk():
           self.assert_node_attributes(node)
           for resource in node.resources:
               self.assert_resource_attributes(resource)
                           
    def assert_node_attributes(self, node):
        fragment = self.get_node_fragment(node)
        if node.type == "content":
            fragment = node.folder.get_fragment(self.site.content_folder)
        elif node.type == "media":
            fragment = node.folder.get_fragment(self.site.folder)
            
        if node.type in ("content", "media"):
            fragment = "/" + fragment.lstrip("/").rstrip("/")
            assert node.url == fragment
            assert node.full_url == settings.SITE_WWW_URL + fragment
        else:    
            assert not node.url
            assert not node.full_url
                
        assert node.source_folder == node.folder
        if not node == self.site and node.type not in ("content", "media"):
            assert not node.target_folder
            assert not node.temp_folder
        else:
            assert node.target_folder.same_as(Folder(
                            os.path.join(settings.DEPLOY_DIR,
                                fragment.lstrip("/"))))
            assert node.temp_folder.same_as(Folder(
                            os.path.join(settings.TMP_DIR, 
                                fragment.lstrip("/"))))
                       
    def assert_resource_attributes(self, resource):
        node = resource.node
        fragment = self.get_node_fragment(node)
        if resource.node.type in ("content", "media"):
            assert (resource.url ==  
                        url.join(node.url, resource.resource_file.name))
            assert (resource.full_url ==  
                        url.join(node.full_url, resource.resource_file.name))
            assert resource.target_file.same_as(
                    File(node.target_folder.child(
                            resource.resource_file.name)))
            assert resource.temp_file.same_as(
                    File(node.temp_folder.child(resource.resource_file.name)))
        else:
            assert not resource.url
            assert not resource.full_url
        
        assert resource.source_file.parent.same_as(node.folder)
        assert resource.source_file.name == resource.resource_file.name
        
    def get_node_fragment(self, node):
        fragment = ''
        if node.type == "content":
            fragment = node.folder.get_fragment(self.site.content_folder)
        elif node.type == "media":
            fragment = node.folder.get_fragment(self.site.folder)
        return fragment
        
class TestSiteInfoContinuous:
    
    def setup_method(self, method):
        self.site = SiteInfo(settings, TEST_SITE.path)
    
    def modification_checker(self):
        from Queue import Empty
        try:
            changes = self.site.queue.get(block=True, timeout=5)
            assert changes
            assert changes['change'] == "Modified"
            assert changes['resource']
            assert changes['resource'].resource_file.path == \
                        self.site.media_folder.child("css/base.css") 
        except Empty:
            print "kashdkjashdk"    
            assert None
            
    def test_modify_content(self):
        from threading import Thread
        from Queue import Queue
        self.site.monitor()
        t = Thread(target=self.modification_checker)
        t.start()
        os.utime(self.site.media_folder.child_folder_with_fragment(
                "css/base.css").path, None)
        t.join()            