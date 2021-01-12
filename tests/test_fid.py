# from unittest import TestCase, main
# from fid_detection import fid_detection, fid_detection_using_pyzbar
#
#
# class TestBarcode(TestCase):
#
#     def testFIDDetection(self):
#
#         expected_result = {'DSC_9735': 'F5921339', 'DSC_9736': 'F5921339', 'DSC_9738': 'F5921339',
#                            'DSC_9740': 'F5921339', 'DSC_9741': 'F5921339', 'DSC_9742': 'F5921339', 'DSC_9743': 'F5921339',
#                            'DSC_9744': 'F5921336', 'DSC_9745': 'F5921338', 'DSC_9746': 'F5921342', 'DSC_9747': 'F5921342',
#                            'DSC_9748': 'F5921344', 'DSC_9749': 'F5921348', 'DSC_9750': 'F5921349', 'DSC_9751': 'F5921350',
#                            'DSC_9752': 'F5921354', 'DSC_9753': 'F5921362', 'DSC_9754': 'F5921355', 'DSC_9755': 'F5921358',
#                            'DSC_9756': 'F5919959', 'DSC_9757': 'F5921370', 'DSC_9758': 'F5921372', 'DSC_9759': 'F5921377',
#                            'DSC_9760': 'F5918585', 'DSC_9761': 'F5921373', 'DSC_9762': 'F5921388', 'DSC_9763': 'F5921389',
#                            'DSC_9764': 'F5921393', 'DSC_9765': 'F5921407', 'DSC_9766': 'F5921394', 'DSC_9767': 'F5918612',
#                            'DSC_9768': 'F5921474', 'DSC_9769': 'F5921475', 'DSC_9770': 'F5921473', 'DSC_9771': 'F5921483',
#                            'DSC_9772': 'F5921484', 'DSC_9773': 'F5921486', 'DSC_9774': 'F5921494', 'DSC_9775': 'F5921493',
#                            'DSC_9776': 'F5921496', 'DSC_9777': 'F5921498', 'DSC_9778': 'F5921495', 'DSC_9779': 'F5921501',
#                            'DSC_9780': 'F5921506', 'DSC_9781': 'F5921508', 'DSC_9781_R': 'F5921508', 'DSC_9782': 'F5921509',
#                            'DSC_9783': 'F5921513', 'DSC_9784': 'F5921516', 'DSC_9785': 'F5921515', 'DSC_9786': 'F5921517',
#                            'DSC_9787': 'F5921520', 'DSC_9788': 'F5921523', 'DSC_9789': 'F5921526', 'DSC_9790': 'F5921527',
#                            'DSC_9791': 'F5921530', 'DSC_9818': 'F5921620' }
#
#         result = fid_detection()
#
#         n_correct = 0
#         n_not_found = 0
#         for key in result:
#             if key in expected_result:
#                 if result[key] == expected_result[key]:
#                     n_correct += 1
#             else:
#                 print(f"Key {key} not found in expected_result dictionary.")
#                 n_not_found += 1
#
#         print(f"Our result: {n_correct}/{len(expected_result)} ({100*n_correct/len(expected_result):.2f}%)")
#         print(f"Not found: {n_not_found} files")
#
#         self.assertEqual(result, expected_result)
#
#     def testFIDDetectionUsingPyZBAR(self):
#
#         expected_result = {'DSC_9735': 'F5921339', 'DSC_9736': 'F5921339', 'DSC_9738': 'F5921339',
#                            'DSC_9740': 'F5921339', 'DSC_9741': 'F5921339', 'DSC_9742': 'F5921339', 'DSC_9743': 'F5921339',
#                            'DSC_9744': 'F5921336', 'DSC_9745': 'F5921338', 'DSC_9746': 'F5921342', 'DSC_9747': 'F5921342',
#                            'DSC_9748': 'F5921344', 'DSC_9749': 'F5921348', 'DSC_9750': 'F5921349', 'DSC_9751': 'F5921350',
#                            'DSC_9752': 'F5921354', 'DSC_9753': 'F5921362', 'DSC_9754': 'F5921355', 'DSC_9755': 'F5921358',
#                            'DSC_9756': 'F5919959', 'DSC_9757': 'F5921370', 'DSC_9758': 'F5921372', 'DSC_9759': 'F5921377',
#                            'DSC_9760': 'F5918585', 'DSC_9761': 'F5921373', 'DSC_9762': 'F5921388', 'DSC_9763': 'F5921389',
#                            'DSC_9764': 'F5921393', 'DSC_9765': 'F5921407', 'DSC_9766': 'F5921394', 'DSC_9767': 'F5918612',
#                            'DSC_9768': 'F5921474', 'DSC_9769': 'F5921475', 'DSC_9770': 'F5921473', 'DSC_9771': 'F5921483',
#                            'DSC_9772': 'F5921484', 'DSC_9773': 'F5921486', 'DSC_9774': 'F5921494', 'DSC_9775': 'F5921493',
#                            'DSC_9776': 'F5921496', 'DSC_9777': 'F5921498', 'DSC_9778': 'F5921495', 'DSC_9779': 'F5921501',
#                            'DSC_9780': 'F5921506', 'DSC_9781': 'F5921508', 'DSC_9781_R': 'F5921508', 'DSC_9782': 'F5921509',
#                            'DSC_9783': 'F5921513', 'DSC_9784': 'F5921516', 'DSC_9785': 'F5921515', 'DSC_9786': 'F5921517',
#                            'DSC_9787': 'F5921520', 'DSC_9788': 'F5921523', 'DSC_9789': 'F5921526', 'DSC_9790': 'F5921527',
#                            'DSC_9791': 'F5921530', 'DSC_9818': 'F5921620'}
#
#         result = fid_detection_using_pyzbar()
#
#         n_correct = 0
#         n_not_found = 0
#         for key in result:
#             if key in expected_result:
#                 if result[key] == expected_result[key]:
#                     n_correct += 1
#             else:
#                 print(f"Key {key} not found in expected_result dictionary.")
#                 n_not_found += 1
#
#         print(f"pyzbar result: {n_correct}/{len(expected_result)} ({100*n_correct/len(expected_result):.2f}%)")
#         print(f"Not found: {n_not_found} files")
#
#         self.assertEqual(result, expected_result)
#
#
# if __name__ == "__main__":
#     main()
